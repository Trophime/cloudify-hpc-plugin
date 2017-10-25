########
# Copyright (c) 2017 MSO4SC - javier.carnero@atos.net
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

""" Holds the slurm functions """
import string
import random
from hpc_plugin.ssh import SshClient


def submit_job(ssh_client, name, job_settings, is_singularity):
    """
    Sends a job to the HPC using Slurm

    @type ssh_client: SshClient
    @param ssh_client: ssh client connected to an HPC login node
    @type name: string
    @param name: name of the job in slurm
    @type job_settings: dictionary
    @param job_settings: dictionary with the job options
    @type is_singularity: bool
    @param is_singularity: True if the job is in a container
    @rtype string
    @return Slurm's job name sent. None if an error arise.
    """
    if not isinstance(ssh_client, SshClient) or not ssh_client.is_open():
        # TODO(emepetres): Raise error
        return False

    if is_singularity:
        script = get_container_script(name, job_settings)
        if script is None:
            # TODO(emepetres): Raise error
            return False

        if not ssh_client.send_command("echo '" + script + "' > " + name +
                                       ".script"):
            # TODO(emepetres): Raise error
            return False
        settings = {
            "type": "SBATCH",
            "command": name + ".script"
        }
    else:
        settings = job_settings

    call = get_call(name, settings)
    if call is None:
        # TODO(emepetres): Raise error
        return False

    return ssh_client.send_command(call)


def clean_job_aux_files(ssh_client, name, job_settings, is_singularity):
    """
    Cleans no more needed job files in the HPC

    @type ssh_client: SshClient
    @param ssh_client: ssh client connected to an HPC login node
    @type name: string
    @param name: name of the job in slurm
    @type job_settings: dictionary
    @param job_settings: dictionary with the job options
    @type is_singularity: bool
    @param is_singularity: True if the job is in a container
    @rtype string
    @return Slurm's job name stopped. None if an error arise.
    """
    if not isinstance(ssh_client, SshClient) or not ssh_client.is_open():
        # TODO(emepetres): Raise error
        return False

    if is_singularity:
        return ssh_client.send_command("rm " + name + ".script")
    return True


def stop_job(ssh_client, name, job_settings, is_singularity):
    """
    Stops a job from the HPC using Slurm

    @type ssh_client: SshClient
    @param ssh_client: ssh client connected to an HPC login node
    @type name: string
    @param name: name of the job in slurm
    @type job_settings: dictionary
    @param job_settings: dictionary with the job options
    @type is_singularity: bool
    @param is_singularity: True if the job is in a container
    @rtype string
    @return Slurm's job name stopped. None if an error arise.
    """
    if not isinstance(ssh_client, SshClient) or not ssh_client.is_open():
        # TODO(emepetres): Raise error
        return False

    # TODO(emepetres): mount slurm stop call
    # call = ""

    # if call is None:
    #     # TODO(emepetres): Raise error
    #     return False

    # return ssh_client.send_command(call)
    return True


def get_jobids_by_name(ssh_client, job_names):
    """
    Get JobID from sacct command

    This function uses sacct command to query Slurm. In this case Slurm
    strongly recommends that the code should performs these queries once
    every 60 seconds or longer. Using these commands contacts the master
    controller directly, the same process responsible for scheduling all
    work on the cluster. Polling more frequently, especially across all
    users on the cluster, will slow down response times and may bring
    scheduling to a crawl. Please don't.
    """
    # TODO(emepetres) set first day of consulting(sacct only check current day)
    call = "sacct -n -o jobname%32,jobid -X --name=" + ','.join(job_names)
    output, exit_code = ssh_client.send_command(call, want_output=True)

    ids = {}
    if exit_code == 0:
        ids = parse_sacct(output)

    return ids


def get_status(ssh_client, job_ids):
    """
    Get Status from sacct command

    This function uses sacct command to query Slurm. In this case Slurm
    strongly recommends that the code should performs these queries once
    every 60 seconds or longer. Using these commands contacts the master
    controller directly, the same process responsible for scheduling all
    work on the cluster. Polling more frequently, especially across all
    users on the cluster, will slow down response times and may bring
    scheduling to a crawl. Please don't.
    """
    # TODO(emepetres) set first day of consulting(sacct only check current day)
    call = "sacct -n -o jobid,state -X --jobs=" + ','.join(job_ids)
    output, exit_code = ssh_client.send_command(call, want_output=True)

    states = {}
    if exit_code == 0:
        states = parse_sacct(output)

    return states


def parse_sacct(sacct_output):
    """ Parse two colums sacct entries into a dict """
    jobs = sacct_output.splitlines()
    parsed = {}
    if jobs and (len(jobs) > 1 or jobs[0] is not ''):
        for job in jobs:
            first, second = job.strip().split()
            parsed[first] = second

    return parsed


def get_container_script(name, job_settings):
    """
    Creates an SBATCH script to run Singularity

    @type name: string
    @param name: name of the job in slurm
    @type job_settings: dictionary
    @param job_settings: dictionary with the container job options
    @rtype string
    @return string to with the sbatch script. None if an error arise.
    """
    # check input information correctness
    if not isinstance(job_settings, dict) or not isinstance(name,
                                                            basestring):
        # TODO(emepetres): Raise error
        return None

    if 'image' not in job_settings or 'command' not in job_settings or\
            'max_time' not in job_settings:
        # TODO(emepetres): Raise error
        return None

    script = '#!/bin/bash -l\n\n'
    # script += '#SBATCH --parsable\n'
    # script += '#SBATCH -J "' + name + '"\n'

    # Slurm settings
    if 'partition' in job_settings:
        script += '#SBATCH -p ' + job_settings['partition'] + '\n'

    if 'nodes' in job_settings:
        script += '#SBATCH -N ' + str(job_settings['nodes']) + '\n'

    if 'tasks' in job_settings:
        script += '#SBATCH -n ' + str(job_settings['tasks']) + '\n'

    if 'tasks_per_node' in job_settings:
        script += '#SBATCH --ntasks-per-node=' + \
            str(job_settings['tasks_per_node']) + '\n'

    if 'max_time' in job_settings:
        script += '#SBATCH -t ' + job_settings['max_time'] + '\n'

    script += '\n'

    # first set modules
    if 'modules' in job_settings:
        script += 'module load'
        for module in job_settings['modules']:
            script += ' ' + module
        script += '\n'

    script += '\nmpirun singularity exec '

    if 'volumes' in job_settings:
        for volume in job_settings['volumes']:
            script += '-B ' + volume
        script += ' '

    # add executable and arguments
    script += job_settings['image'] + ' ' + job_settings['command'] + '\n'

    # disable output
    # script += ' >/dev/null 2>&1';

    return script


def get_call(name, job_settings):
    """
    Generates slurm command line as a string

    @type name: string
    @param name: name of the job in slurm
    @type job_settings: dictionary
    @param job_settings: dictionary with the job options
    @rtype string
    @return string to call slurm with its parameters. None if an error arise.
    """
    # check input information correctness
    if not isinstance(job_settings, dict) or not isinstance(name,
                                                            basestring):
        # TODO(emepetres): Raise error
        return None

    if 'type' not in job_settings or 'command' not in job_settings:
        # TODO(emepetres): Raise error
        return None

    # first set modules
    slurm_call = ''
    if 'modules' in job_settings:
        slurm_call += 'module load'
        for module in job_settings['modules']:
            slurm_call += ' ' + module
        slurm_call += '; '

    if job_settings['type'] == 'SBATCH':
        # sbatch command plus job name
        slurm_call += "sbatch --parsable -J '" + name + "'"
    elif job_settings['type'] == 'SRUN':
        slurm_call += "nohup srun -J '" + name + "'"
    else:
        # TODO(empetres): Raise error
        return None

    # Slurm settings
    if 'partition' in job_settings:
        slurm_call += ' -p ' + job_settings['partition']

    if 'nodes' in job_settings:
        slurm_call += ' -N ' + str(job_settings['nodes'])

    if 'tasks' in job_settings:
        slurm_call += ' -n ' + str(job_settings['tasks'])

    if 'tasks_per_node' in job_settings:
        slurm_call += ' --ntasks-per-node=' + \
                      str(job_settings['tasks_per_node'])

    if 'max_time' in job_settings:
        slurm_call += ' -t ' + job_settings['max_time']
    elif job_settings['type'] == 'SRUN':
        # TODO(empetres): Raise error
        return None

    # add executable and arguments
    slurm_call += ' ' + job_settings['command']

    # disable output
    # slurm_call += ' >/dev/null 2>&1';

    if job_settings['type'] == 'SRUN':
        slurm_call += ' &'

    return slurm_call


def get_random_name(base_name):
    """ Get a random name with a prefix """
    return base_name + '_' + __id_generator()


def __id_generator(size=6, chars=string.digits + string.ascii_letters):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))


"""
  /**
   * We highly recommend that people writing meta-schedulers or that wish to
   * interrogate SLURM in scripts do so using the squeue and sacct commands. We
   * strongly recommend that your code performs these queries once every 60
   * seconds or longer. Using these commands contacts the master controller
   * directly, the same process responsible for scheduling all work on the
   * cluster. Polling more frequently, especially across all users on the
   * cluster, will slow down response times and may bring scheduling to a crawl
   * Please don't.
   */
  int getJobStatus(const ulong& jobid, TaskState* state) const {
    string command = "sacct -n -o state -X -P -j " + std::to_string(jobid);

    ssh_channel channel;
    int rc;
    char buffer[256];
    int nbytes;
    channel = ssh_channel_new(my_ssh_session);
    if (channel == NULL) return SSH_ERROR;
    rc = ssh_channel_open_session(channel);
    if (rc != SSH_OK) {
      ssh_channel_free(channel);
      return rc;
    }
    rc = ssh_channel_request_exec(channel, command.c_str());
    if (rc != SSH_OK) {
      ssh_channel_close(channel);
      ssh_channel_free(channel);
      return rc;
    }

    stringstream output;
    nbytes = ssh_channel_read(channel, buffer, sizeof(buffer), 0);
    while (nbytes > 0) {
      output.write(buffer, nbytes);
      nbytes = ssh_channel_read(channel, buffer, sizeof(buffer), 0);
    }

    if (nbytes < 0) {
      ssh_channel_close(channel);
      ssh_channel_free(channel);
      return SSH_ERROR;
    } else if (output.str().size() > 0) {
      string state_str = output.str();
      state_str.pop_back();  // delete end of line character
      // cout << "DEBUG RECEIVED: " << state_str << endl;

      if (state_str == "PENDING" || state_str == "CONFIGURING") {
        *state = TaskState::TASK_STARTING;
      } else if (state_str == "RUNNING" || state_str == "COMPLETING") {
        *state = TaskState::TASK_RUNNING;

      } else if (state_str == "COMPLETED" || state_str == "PREEMPTED") {
        *state = TaskState::TASK_FINISHED;
      } else if (state_str == "BOOT_FAIL" || state_str == "CANCELLED" ||
                 state_str == "DEADLINE" || state_str == "FAILED" ||
                 state_str == "TIMEOUT") {
        *state = TaskState::TASK_FAILED;
      } else {  // RESIZING, SUSPENDED
        *state = TaskState::TASK_FAILED;
        cout << "ERROR: State '" << state_str << "' could not be recognized."
             << endl;
      }
    }

    ssh_channel_send_eof(channel);
    ssh_channel_close(channel);
    ssh_channel_free(channel);
    return SSH_OK;
  }
};
"""
