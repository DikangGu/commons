# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================
import os

from twitter.common.collections import OrderedSet

from exportable_jvm_library import ExportableJvmLibrary
from jar_dependency import JarDependency
from pants_target import Pants

class JavaThriftLibrary(ExportableJvmLibrary):
  """Defines a target that builds java stubs from a thrift IDL file."""

  _SRC_DIR = 'src/thrift'

  @classmethod
  def _aggregate(cls, name, provides, buildflags, java_thrift_libs):
    all_sources = []
    all_deps = OrderedSet()
    all_excludes = OrderedSet()

    for java_thrift_lib in java_thrift_libs:
      if java_thrift_lib.sources:
        all_sources.extend(java_thrift_lib.sources)
      if java_thrift_lib.resolved_dependencies:
        all_deps.update(dep for dep in java_thrift_lib.jar_dependencies if dep.rev is not None)
      if java_thrift_lib.excludes:
        all_excludes.update(java_thrift_lib.excludes)

    return JavaThriftLibrary(name,
                             all_sources,
                             provides = provides,
                             dependencies = all_deps,
                             excludes = all_excludes,
                             buildflags = buildflags,
                             is_meta = True)

  def __init__(self,
               name,
               sources,
               provides = None,
               dependencies = None,
               excludes = None,
               buildflags = None,
               is_meta = False):

    """name: The name of this module target, addressable via pants via the portion of the spec
        following the colon
    sources: A list of paths containing the thrift source files this module's jar is compiled from
    provides: An optional Dependency object indicating the The ivy artifact to export
    dependencies: An optional list of Dependency objects specifying the binary (jar) dependencies of
        this module.
    excludes: An optional list of dependency exclude patterns to filter all of this module's
        transitive dependencies against.
    buildflags: A list of additional command line arguments to pass to the underlying build system
        for this target"""

    def get_all_deps():
      all_deps = OrderedSet()
      all_deps.update(Pants('3rdparty:commons-lang').resolve())
      all_deps.update(JarDependency(org = 'org.apache.thrift',
                                    name = 'libthrift',
                                    rev = '${thrift.library.version}').resolve())
      all_deps.update(Pants('3rdparty:slf4j-api').resolve())
      if dependencies:
        all_deps.update(dependencies)
      return all_deps

    ExportableJvmLibrary.__init__(self,
                                   JavaThriftLibrary._SRC_DIR,
                                   name,
                                   sources,
                                   provides,
                                   get_all_deps(),
                                   excludes,
                                   buildflags,
                                   is_meta)
    self.is_codegen = True

  def _as_jar_dependency(self):
    return ExportableJvmLibrary._as_jar_dependency(self).withSources()

  def _create_template_data(self):
    allsources = []
    if self.sources:
      allsources += list(os.path.join(JavaThriftLibrary._SRC_DIR, src) for src in self.sources)

    return ExportableJvmLibrary._create_template_data(self).extend(
      allsources = allsources,
    )
