from pybuilder.core import use_plugin, init

use_plugin('python.core')
# build
use_plugin('python.install_dependencies')
use_plugin('python.pydev')
use_plugin('python.distutils')
# quality
use_plugin('python.unittest')
use_plugin('python.coverage')
use_plugin('python.frosted')
use_plugin('python.flake8')
use_plugin('python.pylint')
use_plugin('python.pep8')
# IDE
use_plugin('python.pycharm')

default_task = ['install_dependencies', 'analyze', 'publish']

@init
def set_properties(project):
    project.set_property('frosted_break_build', True)
    project.set_property('flake8_break_build', True)
    project.set_property('pylint_options', ["--max-line-length=79"])

