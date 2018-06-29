########
# Copyright (c) 2017-2018 MSO4SC - javier.carnero@atos.net
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Holds the plugin tasks """

import requests
import traceback
from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from ssh import SshClient
from workload_managers.workload_manager import WorkloadManager
from external_repositories.external_repository import ExternalRepository


@operation
def preconfigure_job(config,
                     external_monitor_entrypoint,
                     external_monitor_port,
                     external_monitor_type,
                     external_monitor_orchestrator_port,
                     job_prefix,
                     simulate,
                     **kwargs):  # pylint: disable=W0613
    """ Set the job with the HPC credentials """
    ctx.logger.info('Preconfiguring HPC job..')

    ctx.source.instance.runtime_properties['credentials'] = \
        config['credentials']
    ctx.source.instance.runtime_properties['external_monitor_entrypoint'] = \
        external_monitor_entrypoint
    ctx.source.instance.runtime_properties['external_monitor_port'] = \
        external_monitor_port
    ctx.source.instance.runtime_properties['external_monitor_type'] = \
        external_monitor_type
    ctx.source.instance.runtime_properties['monitor_orchestrator_port'] = \
        external_monitor_orchestrator_port
    ctx.source.instance.runtime_properties['workload_manager'] = \
        config['workload_manager']
    ctx.source.instance.runtime_properties['simulate'] = simulate
    ctx.source.instance.runtime_properties['job_prefix'] = job_prefix

    ctx.source.instance.runtime_properties['workdir'] = \
        ctx.target.instance.runtime_properties['workdir']


@operation
def create_sregistry(config,
                simulate,
                **kwargs):  # pylint: disable=W0613
    """ Tries to connect to a sregistry node """
    ctx.logger.info('Connecting to sregistry node..')
    for key, value in config.iteritems():
        ctx.logger.info('sregistry: config[%s]=%s' % (key, value) )


@operation
def cleanup_singularity(config, skip, simulate, **kwargs):  # pylint: disable=W0613
    """ Tries to connect to a login node """
    if skip:
        return

    ctx.logger.info('Sregistry Cleaning up...')
    # if not simulate:
    #     workdir = ctx.instance.runtime_properties['workdir']
    #     wm_type = config['workload_manager']
    #     wm = WorkloadManager.factory(wm_type)
    #     if not wm:
    #         raise NonRecoverableError(
    #             "Workload Manager '" +
    #             wm_type +
    #             "' not supported.")
    #     client = SshClient(config['credentials'])
    #     _, exit_code = client.execute_shell_command(
    #         'rm -r ' + workdir,
    #         wait_result=True)
    #     client.close_connection()
    #     ctx.logger.info('..all clean.')
    # else:
    #     ctx.logger.warning('HPC clean up simulated.')
