80s office swap for HRGame / Office map
=======================================

1. Open HRGame in Unreal and load the Office map.
2. Make sure the Python Editor Script Plugin is on (Edit > Plugins, search "Python").
3. Tools > Execute Python Script... and pick replace_blockout_80s.py from this folder.
4. Look it over. Ctrl+Z undoes the whole swap. File > Save All keeps it.

Settings at the top of the script:
  DRY_RUN = True     lists what it would replace without touching anything
  ADD_CHAIRS = True  also puts an 80s swivel chair at each desk

To change colors or details, edit build_models.py and run:  python build_models.py .
then run the Unreal script again (it re-imports over the old meshes).
