from parsl.config import Config
from parsl.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.channels import LocalChannel

transcode_config_local = Config(
    executors=[
        HighThroughputExecutor(
            label="htex_Local",
            worker_debug=True,
            # cores_per_worker=1,
            # storage_access=[HTTPInTaskStaging()],
            provider=LocalProvider(
                channel=LocalChannel(),
                init_blocks=1,
                max_blocks=10,
            ),
        )
    ],
    strategy=None,
)