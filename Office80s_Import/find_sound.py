import unreal, os
out = []
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in ar.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")):
    n = str(ad.asset_name)
    if "roblox" in n.lower() or "walk" in n.lower():
        s = unreal.load_asset(str(ad.package_name))
        out.append("%s|%s|dur=%s|loop=%s" % (ad.package_name, n, s.get_editor_property("duration"), s.get_editor_property("looping")))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "find_sound.txt"), "w").write("\n".join(out) or "none")
