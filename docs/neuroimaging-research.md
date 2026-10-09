# Neuroimaging Research Gateway (first-stage implementation)

## Purpose and status

This is a **research-oriented, non-diagnostic** pathway from a question about brain
structure, function or possible correlates of behaviour to appropriate tools and
testable hypotheses. It offers three executable primitives:

1. `imaging-plan` locally, or `plan_neuroimaging_study` over MCP, builds a
   modality-aware, evidence-conscious study protocol, selecting relevant
   repositories as **uninstalled candidates**, with alternatives and limitations.
2. `imaging-inspect` **locally only**, opens a single NIfTI or DICOM image
   *header* and emits a small, explicit, allowlisted JSON summary of geometry
   and acquisition information. It does **not** inspect voxels or abnormalities.
3. `imaging-mask-volume` **locally only**, measures the physical size of a
   pre-existing, verified, binary 3D NIfTI segmentation/ROI mask. It checks
   millimetre spatial units, affine geometry and binary voxels, and returns
   an explicit voxel count and volume. It does **not** create the mask,
   identify an anatomical region, or infer pathology.

It does **not** currently perform segmentation, brain parcellation, cortical
thickness estimation, tractography, functional connectivity estimation or a
radiology read. These are future adapters requiring validated pipelines and
expert-reviewed quality assurance.

## Local commands

Use only with data you are authorised to analyse.

```bash
pip install -e '.[imaging,dev]'
capability-hunter imaging-plan "Study links between MRI structure and measured cognitive flexibility"
capability-hunter imaging-inspect /private/authorised/deidentified/scan.nii.gz
capability-hunter imaging-inspect /private/authorised/deidentified/one-instance.dcm
capability-hunter imaging-mask-volume /private/authorised/deidentified/verified-roi-mask.nii.gz
pytest -q tests/test_neuroimaging.py
```

Do not use `imaging-inspect` with URLs. It does not upload the scan to GitHub,
ChatGPT, the deployed research API or the MCP service. File paths are input
arguments to the **locally installed** CLI, not to a remote container.

The CLI output excludes filenames, patient fields, names, dates and DICOM UIDs.
The mask-volume command examines an existing mask's voxels entirely locally;
its volumetric result is only as meaningful as the upstream segmentation.
The actual source file remains untouched and **may still contain identifying
information**, including embedded pixel text. The program **does not**
de-identify the original. DICOM inspection is *one instance*, not a full
series. Dimensionality and voxel spacings are not evidence of pathology.

## Research options and validated separation of claims

| Imaging approach | Studied measures | Candidate tools (not installed) | What it cannot establish |
| --- | --- | --- | --- |
| T1/T2/FLAIR structural MRI | anatomy, morphology, lesions, longitudinal comparisons | NiBabel, FreeSurfer, validated MONAI models | Individual character, beliefs, motivation |
| Diffusion MRI | diffusion metrics, modelled white-matter connectivity | QSIPrep, separately validated tractography | Literal wiring or direction of thoughts |
| Task/resting fMRI | BOLD response and statistical associations | fMRIPrep, Nilearn | Direct neural firing, truthfulness or causal motives |
| DICOM/NIfTI ingestion | header and acquisition geometry | pydicom, NiBabel, PyBIDS | Diagnoses or presence/absence of abnormalities |

A proposed full pipeline requires BIDS validation, scanner/protocol assessment,
motion/artifact QC, preprocessing with documented versions, visual QC of
registration, tissue or lesion segmentation, atlas alignment, a prespecified
hypothesis, statistical design and appropriate uncertainty quantification. A
qualified radiologist/neurologist should assess clinical abnormalities.
Longitudinal or lesion evidence can change a hypothesis, but do not by
themselves prove that an anatomical finding caused an observed action.

For perspectives and behaviour, create a **joint evidence matrix** with:
anatomical observation; reproducible measurement; symptom/behaviour definition;
temporal relationship; neurological mechanism; competing psychological,
environmental and medication explanations; confounders; strength of evidence;
and a disconfirming observation. Interpret associations as associations.
Do not diagnose or retrospectively attribute a particular individual's actions
or moral agency from images alone.

Research sources explaining why:

- Poldrack (2006), *Can cognitive processes be inferred from neuroimaging
  data?* DOI: [10.1016/j.tics.2005.12.004](https://doi.org/10.1016/j.tics.2005.12.004)
- Poldrack (2011), *Inferring mental states from neuroimaging data*. DOI:
  [10.1016/j.neuron.2011.11.001](https://doi.org/10.1016/j.neuron.2011.11.001)
- Logothetis and Wandell (2004), *Interpreting the BOLD signal*. DOI:
  [10.1146/annurev.physiol.66.082602.092845](https://doi.org/10.1146/annurev.physiol.66.082602.092845)

## Privacy and safety architecture

- No remote upload or arbitrary file paths in the public MCP interface.
- Never commit image files, scan metadata, case files or personally identifying
  medical data into the repository, Actions artifacts, catalogue or PR.
- The generic MCP planning tool accepts **abstract research questions only**;
  the deployed MCP gateway has not been verified for production-grade
  per-user authentication. Do not submit identifiable health data to it.
- Local execution is separated from scholarly evidence discovery. The planner
  never claims to have read an image.
- Source code from GitHub is untrusted until license/security/code review.
  Upstream implementations are not automatically installed or run.

## Follow-on capability gates

1. **BIDS ingest adapter:** scan-only local sandbox, consent/research ethics,
   anonymisation verification and BIDS validation.
2. **Structural morphology adapter:** T1 pipeline with pinned FreeSurfer or
   equivalent version, atlas/protocol documentation, automated quality metrics,
   visual review, benchmark against known examples; no interpretation without QC.
3. **Functional/diffusion adapter:** select fMRIPrep or QSIPrep by acquisition;
   resource isolation, review of motion/denoising, modelling assumptions and
   statistical tests.
4. **Research synthesis adapter:** link *aggregate-level* published evidence
   to observed metrics with citations and opposing explanations.
5. **Scientific validation:** simulated and public de-identified test sets,
   technical quality metrics, blinded expert review and prospective replication.
6. **Authorised ChatGPT connection:** deploy a private, authenticated, file-scoped
   service with approved imaging input handling before allowing hosted scan
   analysis. No public patient-file URL fetches.

## Upstream discovery record

Repositories checked in live GitHub discovery on 9 October 2026 include
`nipy/nibabel`, `pydicom/pydicom`, `nilearn/nilearn`,
`nipreps/fmriprep`, `PennLINC/qsiprep`, `freesurfer/freesurfer`,
`Project-MONAI/MONAI` and `bids-standard/pybids`.
Licences vary and must be separately reviewed before composing their code
into a distributed application. Metadata and README inspection are
**not** validation of scientific outputs.
