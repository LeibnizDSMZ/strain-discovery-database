from datetime import datetime
from pathlib import Path
from strain_discovery_dataset.utils.data import RunConf

_IMPORT_TIME = datetime.now().strftime("%Y_%m_%d_%H_%M")


def create_run_config() -> RunConf:
    output_path = Path("/data/output/")
    if not output_path.is_dir():
        raise Exception("Output path does not exist, critical error!")
    output_path = output_path.joinpath(_IMPORT_TIME)
    output_path.mkdir(exist_ok=True, parents=True)
    cache = Path("/data/cache")
    cache.mkdir(exist_ok=True)
    return RunConf(output=output_path, cache=cache)


_LOG_FILES: dict[str, Path] = {}


def get_log_file(log_id: str, /) -> Path:
    log_path = _LOG_FILES.get(log_id)
    if log_path is not None:
        return log_path
    output_path = Path("/data/output/")
    if not output_path.is_dir():
        raise Exception("Output path does not exist, critical error!")
    output_path = output_path.joinpath(_IMPORT_TIME, "logs")
    output_path.mkdir(exist_ok=True, parents=True)
    log_path = output_path.joinpath(f"{log_id}.log")
    _LOG_FILES[log_id] = log_path
    return log_path
