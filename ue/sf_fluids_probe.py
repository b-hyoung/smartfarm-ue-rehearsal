"""NiagaraFluids 플러그인 콘텐츠 조사 — 쓸 만한 Grid3D 기체 템플릿과 노출 파라미터.

    py ue/ue_exec.py -f ue/sf_fluids_probe.py
"""
import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/NiagaraFluids", recursive=True)
systems = [a for a in assets if str(a.asset_class_path.asset_name) == "NiagaraSystem"]
print("SF_FLUIDS: NiagaraSystem %d개" % len(systems))
for a in systems:
    print("  %s" % a.package_name)

# 대표 후보의 사용자 파라미터 나열
for cand in systems:
    name = str(cand.package_name)
    if "Gas" not in name and "gas" not in name:
        continue
    sys_obj = unreal.load_asset(name)
    if not sys_obj:
        continue
    print("SF_FLUIDS: === %s 노출 파라미터 ===" % name)
    try:
        eps = sys_obj.get_editor_property("exposed_parameters")
        # FNiagaraUserRedirectionParameterStore 는 파이썬 노출이 제한적 — to_string 시도
        print("  (store) %s" % eps)
    except Exception as e:
        print("  exposed_parameters 접근 불가: %s" % e)
