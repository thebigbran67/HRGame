import unreal, os
ar = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for ad in ar.get_assets_by_path("/Game", recursive=True):
    if "roblox" in str(ad.asset_name).lower():
        out.append("%s %s" % (ad.get_soft_object_path() if hasattr(ad, "get_soft_object_path") else ad.package_name, ad.asset_class_path.asset_name))
        a = unreal.load_asset(str(ad.package_name))
        try:
            out.append("  duration %.2f" % a.get_editor_property("duration"))
        except Exception:
            pass
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "find_roblox.txt"), "w").write("\n".join(out) or "none")
