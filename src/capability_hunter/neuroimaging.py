"""Local-only, metadata-level imaging inspection and research question planning.

No clinical diagnosis, behaviour decoding, patient data upload or automated image
segmentation occurs here. The hosted MCP exposes the generic research plan only.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

RESEARCH_TOOLS = {
    "dicom_metadata": "https://github.com/pydicom/pydicom",
    "nifti_io": "https://github.com/nipy/nibabel",
    "bids": "https://github.com/bids-standard/pybids",
    "structural_morphometry": "https://github.com/freesurfer/freesurfer",
    "functional_preprocessing": "https://github.com/nipreps/fmriprep",
    "functional_statistics": "https://github.com/nilearn/nilearn",
    "diffusion_preprocessing": "https://github.com/PennLINC/qsiprep",
    "segmentation_research": "https://github.com/Project-MONAI/MONAI",
}

MODALITIES = {
    "structural": {
        "inputs": ["T1-weighted MRI", "T2/FLAIR MRI where indicated", "radiology reports"],
        "questions": ["brain anatomy", "regional morphometry", "lesion localisation", "longitudinal change"],
        "candidate_stack": ["nibabel", "FreeSurfer", "MONAI (only with a validated model)"],
        "limits": "Morphometric measures are not diagnoses and do not reveal personality, perspective, intent or an individual's cause of behaviour.",
    },
    "diffusion": {
        "inputs": ["multi-direction diffusion MRI", "b-values and b-vectors"],
        "questions": ["white-matter diffusion metrics", "tractography model fit"],
        "candidate_stack": ["QSIPrep", "tractography software validated for the protocol"],
        "limits": "Tractography estimates model-dependent paths, not proven neuronal connections or thought content.",
    },
    "functional": {
        "inputs": ["task/resting-state BOLD fMRI", "task design or physiological confounds"],
        "questions": ["group-level task contrasts", "functional connectivity", "association with measured phenotypes"],
        "candidate_stack": ["fMRIPrep", "Nilearn"],
        "limits": "BOLD is an indirect haemodynamic signal; activation patterns cannot establish beliefs or motives.",
    },
    "clinical": {
        "inputs": ["clinical history", "properly reviewed MRI/CT", "medication/timing information"],
        "questions": ["differential hypotheses", "evidence for or against structural correlates"],
        "candidate_stack": ["pydicom", "nibabel", "specialist radiology/neurology review"],
        "limits": "Clinical interpretation requires a qualified clinician, complete sequences, reports and context.",
    },
}


def _detect_modalities(question: str) -> list[str]:
    checks = {
        "structural": r"\b(structur\w*|anatomi\w*|morphometr\w*|cortical|hippocamp\w*|lesion\w*|tumou?r\w*|atroph\w*|flair|volume\w*|mri|ct\b)",
        "diffusion": r"\b(diffusion|dti|dwi|white.matter|tractograph\w*|connectom\w*)\b",
        "functional": r"\b(fmri|bold|functional|connectiv\w*|resting.state|activation)\b",
    }
    found = [k for k, pattern in checks.items() if re.search(pattern, question, re.I)]
    return found or ["structural", "clinical"]


def plan_neuroimaging_research(question: str) -> dict:
    """Evidence-aware *protocol*, not an individual diagnosis or image analysis."""
    if not isinstance(question, str) or not 5 <= len(question.strip()) <= 3000:
        raise ValueError("Question must contain 5–3000 characters")
    selected = _detect_modalities(question)
    behavioural = bool(re.search(
        r"\b(behavio\w*|belief\w*|perspective\w*|motivat\w*|intent\w*|decision\w*|"
        r"emotion\w*|personality|psych\w*|agency|why did|mental.state)\b", question, re.I))
    if behavioural and "clinical" not in selected:
        selected.append("clinical")
    return {
        "status": "RESEARCH_PROTOCOL_ONLY_NO_SCAN_INTERPRETED",
        "question": question.strip(),
        "modalities": {key: MODALITIES[key] for key in selected},
        "relevant_upstream_repositories_not_installed": RESEARCH_TOOLS,
        "study_design": [
            "State the exact observable imaging measurement and the independently defined behavioural or clinical outcome.",
            "Check consent, acquisition metadata, de-identification, motion/artifact and quality-control reports.",
            "Identify anatomical or functional hypotheses before analysis; specify comparator, timing and covariates.",
            "Use validated segmentation/preprocessing, independent visual QC and appropriate multiple-comparison corrections.",
            "Compare competing biological, psychological, situational and social explanations.",
            "Separate individual clinical observations from population-level statistical associations and replication evidence.",
        ],
        "confounds": [
            "Age, development, sex, individual variation, scanner/protocol, motion, prior illness",
            "Medication and treatment, sleep, stress, comorbidity, substance exposure, timing",
            "Selection bias, reverse causality, multiple testing and data leakage",
        ],
        "behavioural_inference_guard": (
            "A scan cannot tell us what someone thought, believed, intended or why they acted. "
            "Neuroanatomical or imaging associations can motivate bounded hypotheses, "
            "not a retrospective causal or moral verdict."
        ) if behavioural else (
            "Imaging markers alone do not establish diagnosis or causal explanation; clinical and methodological review is needed."
        ),
        "data_privacy": "Do not put identifiable scans, DICOM headers, personal case text or filenames into the public repo, issue tracker or hosted research gateway.",
        "evidence_levels": [
            "Observed: scan acquisition and measured image-derived variables after QC",
            "Validated: clinician-reviewed finding or independently reproduced measurement",
            "Associative: statistical relationship under an explicit design",
            "Hypothesis: plausible mechanism requiring external tests",
            "Unknown: individual motivation, belief and causation not resolved by imaging",
        ],
        "execution": "No third-party imaging pipeline is executed by this planner.",
    }


def _finite(value: object) -> float | None:
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return round(number, 5) if math.isfinite(number) else None


def _finite_list(items: object, limit: int = 4) -> list[float | None]:
    try:
        return [_finite(item) for item in list(items)[:limit]]
    except (ValueError, TypeError):
        return []


def inspect_local_imaging_header(filename: str) -> dict:
    """Inspect a single local NIfTI/DICOM header without returning PHI or path.

    This intentionally does not read pixel arrays, derive diagnoses, identify
    lesions, de-identify the underlying original file or send files anywhere.
    Never expose this function over an unauthenticated remote API/MCP.
    """
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("Provide a local file path")
    path = Path(filename).expanduser()
    if not path.is_file():
        raise ValueError("Local imaging file not found")
    name = path.name.lower()
    common = {
        "status": "LOCAL_HEADER_ONLY_NO_INTERPRETATION",
        "contains_patient_identifiers": False,  # refers to RETURN VALUE, not original!
        "source_file_is_deidentified": "NOT_CHECKED",
        "diagnosis_or_behaviour_inferred": False,
        "note": "Only selected geometry/acquisition information; no path, name, UID, dates or patient tags are returned. Input file may still contain PHI.",
    }
    if name.endswith((".nii", ".nii.gz")):
        try:
            import nibabel as nib
        except ImportError as exc:
            raise RuntimeError("Install optional local package: pip install nibabel") from exc
        image = nib.load(str(path))
        dims = [int(v) for v in image.shape]
        if len(dims) < 3 or len(dims) > 7:
            raise ValueError("Unsupported NIfTI dimensionality")
        zooms = _finite_list(image.header.get_zooms(), limit=7)
        return {
            **common, "format": "NIfTI", "dimensions": dims,
            "voxel_zooms": zooms, "voxel_units": "See original image header; do not assume spatial/temporal units.",
            "volume_count": dims[3] if len(dims) > 3 else 1,
            "quality_checks_needed": [
                "Check orientation, units and spatial transforms",
                "Check coverage, artifacts, motion, registration and sequence type",
                "Review with a qualified imaging researcher/clinician",
            ],
        }
    if name.endswith((".dcm", ".dicom")):
        try:
            import pydicom
        except ImportError as exc:
            raise RuntimeError("Install optional local package: pip install pydicom") from exc
        allowed = ["Modality", "Rows", "Columns", "PixelSpacing", "SliceThickness", "MagneticFieldStrength", "RepetitionTime", "EchoTime"]
        dataset = pydicom.dcmread(str(path), stop_before_pixels=True, specific_tags=allowed)
        return {
            **common, "format": "DICOM",
            "modality": str(getattr(dataset, "Modality", "UNKNOWN"))[:12],
            "rows": int(getattr(dataset, "Rows", 0) or 0),
            "columns": int(getattr(dataset, "Columns", 0) or 0),
            "pixel_spacing": _finite_list(getattr(dataset, "PixelSpacing", ())),
            "slice_thickness": _finite(getattr(dataset, "SliceThickness", None)),
            "magnetic_field_strength": _finite(getattr(dataset, "MagneticFieldStrength", None)),
            "repetition_time": _finite(getattr(dataset, "RepetitionTime", None)),
            "echo_time": _finite(getattr(dataset, "EchoTime", None)),
            "quality_checks_needed": [
                "Single DICOM instance is not a complete examination",
                "Check series completeness, orientation, units, artifacts and acquisition context",
                "A header is not enough to identify structural abnormalities",
            ],
        }
    raise ValueError("Supported local formats: .nii, .nii.gz, .dcm, .dicom")
