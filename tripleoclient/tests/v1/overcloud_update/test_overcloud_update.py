#   Copyright 2015 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import mock

from osc_lib.tests.utils import ParserException
from tripleoclient import constants
from tripleoclient import exceptions
from tripleoclient.tests.v1.overcloud_update import fakes
from tripleoclient.v1 import overcloud_update


class TestOvercloudUpdatePrepare(fakes.TestOvercloudUpdatePrepare):

    def setUp(self):
        super(TestOvercloudUpdatePrepare, self).setUp()

        # Get the command object to test
        app_args = mock.Mock()
        app_args.verbose_level = 1
        self.cmd = overcloud_update.UpdatePrepare(self.app, app_args)

        uuid4_patcher = mock.patch('uuid.uuid4', return_value="UUID4")
        self.mock_uuid4 = uuid4_patcher.start()
        self.addCleanup(self.mock_uuid4.stop)

    @mock.patch('tripleoclient.utils.get_stack',
                autospec=True)
    @mock.patch('tripleoclient.v1.overcloud_update.UpdatePrepare.log',
                autospec=True)
    @mock.patch('tripleoclient.workflows.package_update.update',
                autospec=True)
    @mock.patch('os.path.abspath')
    @mock.patch('yaml.load')
    @mock.patch('shutil.copytree', autospec=True)
    @mock.patch('six.moves.builtins.open')
    @mock.patch('tripleoclient.v1.overcloud_deploy.DeployOvercloud.'
                '_deploy_tripleo_heat_templates', autospec=True)
    def test_update_out(self, mock_deploy, mock_open, mock_copy, mock_yaml,
                        mock_abspath, mock_update, mock_logger,
                        mock_get_stack):
        mock_stack = mock.Mock()
        mock_stack.stack_name = 'overcloud'
        mock_get_stack.return_value = mock_stack
        mock_abspath.return_value = '/home/fake/my-fake-registry.yaml'
        mock_yaml.return_value = {'fake_container': 'fake_value'}

        argslist = ['--stack', 'overcloud', '--templates',
                    '--container-registry-file', 'my-fake-registry.yaml']
        verifylist = [
            ('stack', 'overcloud'),
            ('templates', constants.TRIPLEO_HEAT_TEMPLATES),
            ('container_registry_file', 'my-fake-registry.yaml')
        ]

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)
        with mock.patch('os.path.exists') as mock_exists, \
                mock.patch('os.path.isfile') as mock_isfile:
            mock_exists.return_value = True
            mock_isfile.return_value = True
            self.cmd.take_action(parsed_args)
            mock_update.assert_called_once_with(
                self.app.client_manager,
                container='overcloud',
                container_registry={'fake_container': 'fake_value'},
                ceph_ansible_playbook='/usr/share/ceph-ansible'
                                      '/site-docker.yml.sample'
            )

    @mock.patch('tripleoclient.workflows.package_update.update',
                autospec=True)
    @mock.patch('six.moves.builtins.open')
    @mock.patch('os.path.abspath')
    @mock.patch('yaml.load')
    @mock.patch('shutil.copytree', autospec=True)
    @mock.patch('tripleoclient.v1.overcloud_deploy.DeployOvercloud.'
                '_deploy_tripleo_heat_templates', autospec=True)
    def test_update_failed(self, mock_deploy, mock_copy, mock_yaml,
                           mock_abspath, mock_open, mock_update):
        mock_update.side_effect = exceptions.DeploymentError()
        mock_abspath.return_value = '/home/fake/my-fake-registry.yaml'
        mock_yaml.return_value = {'fake_container': 'fake_value'}
        argslist = ['--stack', 'overcloud', '--templates',
                    '--container-registry-file', 'my-fake-registry.yaml']
        verifylist = [
            ('stack', 'overcloud'),
            ('templates', constants.TRIPLEO_HEAT_TEMPLATES),
            ('container_registry_file', 'my-fake-registry.yaml')
        ]
        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        with mock.patch('os.path.exists') as mock_exists, \
                mock.patch('os.path.isfile') as mock_isfile:
            mock_exists.return_value = True
            mock_isfile.return_value = True
            self.assertRaises(exceptions.DeploymentError,
                              self.cmd.take_action, parsed_args)


class TestOvercloudUpdateRun(fakes.TestOvercloudUpdateRun):

    def setUp(self):
        super(TestOvercloudUpdateRun, self).setUp()

        # Get the command object to test
        app_args = mock.Mock()
        app_args.verbose_level = 1
        self.cmd = overcloud_update.UpdateRun(self.app, app_args)

        uuid4_patcher = mock.patch('uuid.uuid4', return_value="UUID4")
        self.mock_uuid4 = uuid4_patcher.start()
        self.addCleanup(self.mock_uuid4.stop)

    @mock.patch('tripleoclient.workflows.package_update.update_ansible',
                autospec=True)
    @mock.patch('os.path.expanduser')
    @mock.patch('oslo_concurrency.processutils.execute')
    @mock.patch('six.moves.builtins.open')
    def test_update_with_playbook_and_user(self, mock_open, mock_execute,
                                           mock_expanduser, update_ansible):
        mock_expanduser.return_value = '/home/fake/'
        argslist = ['--roles', 'Compute',
                    '--playbook', 'fake-playbook.yaml',
                    '--ssh-user', 'tripleo-admin']
        verifylist = [
            ('roles', 'Compute'),
            ('static_inventory', None),
            ('playbook', 'fake-playbook.yaml'),
            ('ssh_user', 'tripleo-admin')
        ]

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)
        with mock.patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            self.cmd.take_action(parsed_args)
            update_ansible.assert_called_once_with(
                self.app.client_manager,
                nodes='Compute',
                inventory_file=mock_open().read(),
                playbook='fake-playbook.yaml',
                ansible_queue_name=constants.UPDATE_QUEUE,
                node_user='tripleo-admin',
                skip_tags=''
            )

    @mock.patch('tripleoclient.workflows.package_update.update_ansible',
                autospec=True)
    @mock.patch('os.path.expanduser')
    @mock.patch('oslo_concurrency.processutils.execute')
    @mock.patch('six.moves.builtins.open')
    def test_update_roles_with_all_playbooks(self, mock_open, mock_execute,
                                             mock_expanduser, update_ansible):
        mock_expanduser.return_value = '/home/fake/'
        argslist = ['--roles', 'Compute', '--playbook', 'all']
        verifylist = [
            ('roles', 'Compute'),
            ('static_inventory', None),
            ('playbook', 'all')
        ]

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)
        with mock.patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            self.cmd.take_action(parsed_args)
            for book in constants.MINOR_UPDATE_PLAYBOOKS:
                update_ansible.assert_any_call(
                    self.app.client_manager,
                    nodes='Compute',
                    inventory_file=mock_open().read(),
                    playbook=book,
                    ansible_queue_name=constants.UPDATE_QUEUE,
                    node_user='heat-admin',
                    skip_tags=''
                )

    @mock.patch('tripleoclient.workflows.package_update.update_ansible',
                autospec=True)
    @mock.patch('os.path.expanduser')
    @mock.patch('oslo_concurrency.processutils.execute')
    @mock.patch('six.moves.builtins.open')
    def test_update_nodes_with_all_playbooks(
            self, mock_open, mock_execute, mock_expanduser, update_ansible):
        mock_expanduser.return_value = '/home/fake/'
        argslist = ['--nodes', 'compute-0, compute-1']
        verifylist = [
            ('static_inventory', None),
            ('playbook', 'all'),
            ('nodes', 'compute-0, compute-1')
        ]
        parsed_args = self.check_parser(self.cmd, argslist, verifylist)
        with mock.patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            self.cmd.take_action(parsed_args)
            for book in constants.MINOR_UPDATE_PLAYBOOKS:
                update_ansible.assert_any_call(
                    self.app.client_manager,
                    nodes='compute-0, compute-1',
                    inventory_file=mock_open().read(),
                    playbook=book,
                    ansible_queue_name=constants.UPDATE_QUEUE,
                    node_user='heat-admin',
                    skip_tags=''
                )

    @mock.patch('tripleoclient.workflows.package_update.update_ansible',
                autospec=True)
    @mock.patch('os.path.expanduser')
    @mock.patch('oslo_concurrency.processutils.execute')
    @mock.patch('six.moves.builtins.open')
    def test_update_with_no_nodes_or_roles(self, mock_open, mock_execute,
                                           mock_expanduser, update_ansible):
        mock_expanduser.return_value = '/home/fake/'
        argslist = []
        verifylist = [
            ('static_inventory', None),
            ('playbook', 'all')
        ]
        self.assertRaises(ParserException, lambda: self.check_parser(
            self.cmd, argslist, verifylist))

    @mock.patch('tripleoclient.workflows.package_update.update_ansible',
                autospec=True)
    @mock.patch('os.path.expanduser')
    @mock.patch('oslo_concurrency.processutils.execute')
    @mock.patch('six.moves.builtins.open')
    def test_update_with_nodes_and_roles(self, mock_open, mock_execute,
                                         mock_expanduser, update_ansible):
        mock_expanduser.return_value = '/home/fake/'
        argslist = ['--roles', 'Controller',
                    '--nodes', 'overcloud-controller-1']
        verifylist = [
            ('roles', 'Controller'),
            ('nodes', 'overcloud-controller-1'),
            ('static_inventory', None),
            ('playbook', 'all')
        ]
        self.assertRaises(ParserException, lambda: self.check_parser(
            self.cmd, argslist, verifylist))


class TestOvercloudUpdateConverge(fakes.TestOvercloudUpdateConverge):

    def setUp(self):
        super(TestOvercloudUpdateConverge, self).setUp()

        # Get the command object to test
        app_args = mock.Mock()
        app_args.verbose_level = 1
        self.cmd = overcloud_update.UpdateConverge(self.app, app_args)

    @mock.patch(
        'tripleoclient.v1.overcloud_deploy.DeployOvercloud.take_action')
    def test_update_converge(self, deploy_action):
        argslist = ['--templates', '--stack', 'cloud']
        verifylist = [
            ('stack', 'cloud')
        ]
        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        with mock.patch('os.path.exists') as mock_exists, \
                mock.patch('os.path.isfile') as mock_isfile:
            mock_exists.return_value = True
            mock_isfile.return_value = True
            self.cmd.take_action(parsed_args)
            assert('/usr/share/openstack-tripleo-heat-templates/'
                   'environments/lifecycle/update-converge.yaml'
                   in parsed_args.environment_files)
            deploy_action.assert_called_once_with(parsed_args)
