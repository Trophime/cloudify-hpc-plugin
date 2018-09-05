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
from cloudify import ctx
from cloudify.state import ctx_parameters as inputs

ctx.logger.info("Creating sregistry node..")

props = ctx.node.properties
ctx.logger.info("sregistry: config = {}".format(props["config"]))

# for key, value in config.iteritems():
#     ctx.logger.info('sregistry: config[%s]=%s' % (key, value) )
 
for key, value in props['config'].iteritems():
    ctx.instance.runtime_properties[key] = value
