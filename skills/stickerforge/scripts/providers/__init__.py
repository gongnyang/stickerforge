"""provider 규약: 모듈마다 generate(job, cfg) -> dict.
job = {id, prompt, refs:[절대경로], out:절대경로, transparent:bool, log:절대경로}
cfg = spec.json의 provider 설정(model, effort, timeout, size_px 등)
반환 = {ok:bool, thread_id:str, error:str, note:str}. 성공하면 job['out']에 PNG가 있다."""
import importlib


def get(name):
    return importlib.import_module(f"providers.{name}")
