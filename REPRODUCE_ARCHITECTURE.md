# Architectural completion pipeline

The final `.blend` is self-contained and editable. The delivery `source/` folder preserves authoring scripts and canonical specifications; it is not a copy of the full photogrammetry cache. A from-video rebuild starts with `REPRODUCE_AERIAL.md` and requires the user's original video, the previous aerial-continuation `.blend`, registered source frames, and visibility masks in the working repository.

## Frozen inputs and assumptions

`work/buildings/visibility/architecture_visibility.json` is the final 299-unit geometry specification. `roof_annotations.json` retains source-image roof traces and duplicate annotations. `roof_geometry_corrections.json` records inferred regularization. `surface_finishes.json` preserves source-sampled dominant colours, and `observed_roof_fixtures.json` holds localized fixtures. `visibility/poses.json` and `visibility/masks/` provide reference projection metadata; `ground_context.npz` stores approximate local ground support. Hidden dimensions and opening layouts are authorized estimates.

Blender 5.2.1 supplied Python/NumPy for scene generation. The local video environment supplied OpenCV, Pillow, SciPy and pycolmap for preparation and review cards. The Chinese card font is STHeiti Medium on macOS.

## Authoring order

1. Produce roof and facade source data with `prepare_architecture.py`, `refine_visible_facades.py`, the inventory/control scripts and the documented manual correction data. For the final state, use the committed `architecture_visibility.json`; do not overwrite it by rerunning initial candidate extraction.
2. Load `outputs/aerial-continuation/Village_Aerial_Continuation.blend` and run `work/build_architecture.py`. Use `BUILD_IDS` as a comma-separated ID list, `ARCHITECTURE_OUT=work/buildings/<batch>` and `SKIP_RENDER=1`. Build batches of around 60–80 units. The existing four batch ID files partition all 299 units.
3. Open each generated batch and run `work/condense_architecture_components.py` with `BATCH_FOLDER=<batch>`. This preserves geometry and records component ranges while reducing object count. Keep flat face shading for planar walls.
4. Run `work/assemble_architecture_batches.py` from the repository root. It copies organized batches into local data IDs. Do not append raw 140,000-object batches; Blender ID remapping is prohibitively slow.
5. Run `work/clean_architecture_materials.py` on the assembled scene to apply continuous source-colour finishes, then `work/finish_roof_seams.py` to trim metal roof seams. The final corrections were built in small batches and merged with `merge_final_architecture_corrections.py`; from the final specifications they are already included in a fresh build.
6. Reopen the saved candidate file with `work/validate_architecture.py`; render `work/building_gallery.py` and `work/render_architecture_overview.py`. `GALLERY_PAGES` selects one-based comma-separated pages for changed geometry. Inspect every unit from both views and inspect representative close views. Generation success does not constitute visual acceptance.
7. Create `visual_review.json` only after actual visual inspection; use `work/finalize_architecture.py` to remove superseded coarse/proxy collections and save `Village_Reconstructed.blend`. Reopen that file and rerun the validator.
8. Run `work/package_building_review.py`, `work/write_architecture_report.py` and `work/export_architecture_delivery.py`. Verify the HTML interaction, links and local images in a browser, then regenerate checksums and ZIP after recording browser checks.

## Direct revalidation

From the repository root, open the saved deliverable using the installed Blender executable:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  -b outputs/building-quality/Village_Reconstructed.blend -t 6 \
  --python work/validate_architecture.py
```

The validation script reads the final inventory under `work/buildings/visibility/`. It checks all building IDs, component structure, wall bounds, finite and nondegenerate geometry, planar shading, packed assets, local data, and the unchanged landmark hash. It does not prove physical dimensions or unobserved real-world details.
