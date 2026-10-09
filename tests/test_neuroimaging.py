"""Synthetic and mocked tests: no patient images and no third-party models."""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from capability_hunter.domain_router import plan_specialist_tools
from capability_hunter.neuroimaging import (
    inspect_local_imaging_header,
    plan_neuroimaging_research,
)
from capability_hunter.task_router import compile_task


def test_structural_mri_routes_to_specialist_not_microscopy():
    plan = plan_specialist_tools("Analyse structural brain MRI morphometry and behaviour")
    assert plan["domain"] == "biology"
    assert "neuroimaging" in plan["subfields"]
    assert plan["provisional_first_repo"] == "nipy/nibabel"
    assert all(x["status"] == "CURATED_CANDIDATE_NOT_INSTALLED"
               for x in plan["suggested_repositories_not_connected"])


def test_medical_imaging_alone_classifies_as_biology():
    plan = plan_specialist_tools("Inspect medical imaging DICOM data")
    assert "neuroimaging" in plan["subfields"]


def test_compiler_picks_neuroimaging_and_does_not_pretend_execution():
    result = compile_task("Examine fMRI and diffusion MRI for functional connectivity")
    assert "neuroimaging" in result["specialist_route"]["subfields"]
    assert result["execution_status"] == "NOT_EXECUTED_BY_COMPILER"


def test_protocol_guards_against_mindreading_and_causal_overclaim():
    plan = plan_neuroimaging_research(
        "Can structural MRI explain a person's perspective or motivation?"
    )
    assert plan["status"] == "RESEARCH_PROTOCOL_ONLY_NO_SCAN_INTERPRETED"
    assert "structural" in plan["modalities"]
    assert "clinical" in plan["modalities"]
    assert "cannot tell us what someone thought" in plan["behavioural_inference_guard"]
    assert plan["execution"].startswith("No third-party imaging")


@pytest.mark.parametrize("bad", ["", "   ", None, 1, "x" * 3001])
def test_invalid_research_question(bad):
    with pytest.raises(ValueError):
        plan_neuroimaging_research(bad)


def test_fake_nifti_header_local_only(tmp_path, monkeypatch):
    fname = tmp_path / "person_name_MRI.nii.gz"
    fname.write_bytes(b"synthetic-no-real-imaging")
    header = SimpleNamespace(get_zooms=lambda: (1.0, 1.0, 1.5, 0.8))
    image = SimpleNamespace(shape=(20, 30, 40, 100), header=header)
    monkeypatch.setitem(sys.modules, "nibabel", SimpleNamespace(load=lambda path: image))
    data = inspect_local_imaging_header(str(fname))
    assert data["dimensions"] == [20, 30, 40, 100]
    assert data["volume_count"] == 100
    assert "path" not in data and "patient" not in str(data).lower().replace(
        "contains_patient_identifiers", "").replace("patient tags", ""
    )
    assert data["diagnosis_or_behaviour_inferred"] is False


def test_fake_dicom_header_drops_phi_and_pixels(tmp_path, monkeypatch):
    fname = tmp_path / "identified_scan.dcm"
    fname.write_bytes(b"synthetic-no-real-imaging")
    observed = []

    def fake_read(path, **kwargs):
        observed.append(kwargs)
        return SimpleNamespace(
            PatientName="NAME PRIVATE",
            PatientID="SECRET42",
            PixelData=b"should-never-be-read",
            Modality="MR",
            Rows=100,
            Columns=120,
            PixelSpacing=[0.5, 0.5],
            SliceThickness=1.2,
            EchoTime=3.1,
        )

    monkeypatch.setitem(sys.modules, "pydicom", SimpleNamespace(dcmread=fake_read))
    result = inspect_local_imaging_header(str(fname))
    assert result["format"] == "DICOM"
    assert result["modality"] == "MR"
    assert result["rows"] == 100
    assert "NAME PRIVATE" not in str(result)
    assert "SECRET42" not in str(result)
    assert observed[0]["stop_before_pixels"] is True
    assert "PatientName" not in observed[0]["specific_tags"]
    assert "PatientID" not in observed[0]["specific_tags"]


def test_unrecognised_modality_not_echoed(tmp_path, monkeypatch):
    fname = tmp_path / "test.dcm"
    fname.write_bytes(b"fake")
    ds = SimpleNamespace(Modality="PATIENT NAME", Rows=4, Columns=5)
    monkeypatch.setitem(sys.modules, "pydicom", SimpleNamespace(
        dcmread=lambda *_args, **_kwargs: ds))
    result = inspect_local_imaging_header(str(fname))
    assert result["modality"] == "UNKNOWN"
    assert "PATIENT NAME" not in str(result)


def test_unsupported_format_and_nonexistent_path(tmp_path):
    file = tmp_path / "scan.jpg"
    file.write_bytes(b"not a scan")
    with pytest.raises(ValueError, match="Supported local formats"):
        inspect_local_imaging_header(str(file))
    with pytest.raises(ValueError, match="not found"):
        inspect_local_imaging_header(str(tmp_path / "not_found.nii"))


def test_quantitative_binary_mask_volume_from_real_synthetic_nifti(tmp_path):
    import numpy as np
    import nibabel as nib
    from capability_hunter.neuroimaging import measure_local_binary_roi_mask

    voxels = np.zeros((3, 4, 5), dtype=np.uint8)
    voxels[1, 2, 1:3] = 1
    affine = np.diag([2.0, 3.0, 4.0, 1.0])
    img = nib.Nifti1Image(voxels, affine=affine)
    img.header.set_xyzt_units(xyz="mm")
    private_filename = tmp_path / "PERSON_ID_123_mask.nii.gz"
    nib.save(img, str(private_filename))

    result = measure_local_binary_roi_mask(str(private_filename))
    assert result["mask_voxel_count"] == 2
    assert result["voxel_volume_mm3"] == 24.0
    assert result["mask_volume_mm3"] == 48.0
    assert result["mask_volume_ml"] == 0.048
    assert "PERSON_ID_123" not in str(result)
    assert result["raw_image_uploaded"] is False


def test_quantitative_mask_rejects_unsegmented_data(tmp_path):
    import numpy as np
    import nibabel as nib
    from capability_hunter.neuroimaging import measure_local_binary_roi_mask

    img = nib.Nifti1Image(np.full((3, 3, 3), 0.5), affine=np.eye(4))
    img.header.set_xyzt_units(xyz="mm")
    filename = tmp_path / "invalid_mask.nii"
    nib.save(img, str(filename))
    with pytest.raises(ValueError, match="must be binary"):
        measure_local_binary_roi_mask(str(filename))


def test_quantitative_mask_requires_explicit_spatial_units(tmp_path):
    import numpy as np
    import nibabel as nib
    from capability_hunter.neuroimaging import measure_local_binary_roi_mask

    img = nib.Nifti1Image(np.ones((2, 2, 2), dtype=np.uint8), affine=np.eye(4))
    img.header.set_xyzt_units(xyz="unknown")
    filename = tmp_path / "unknown_units.nii.gz"
    nib.save(img, str(filename))
    with pytest.raises(ValueError, match="millimetre spatial units"):
        measure_local_binary_roi_mask(str(filename))
