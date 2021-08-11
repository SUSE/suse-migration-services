import os
import configparser
import logging

from suse_migration_services.defaults import Defaults


def remote_repos():
    log = logging.getLogger(Defaults.get_migration_log_name())
    repos_path = '/etc/zypp/repos.d'
    no_remote_repos = []

    if os.path.exists(repos_path):
        repos_list = os.listdir(repos_path)
        config = configparser.RawConfigParser()
        if not repos_list:
            log.error('No repositories in {}'.format(repos_path))
            return

        migration_accepted_prefixes = ('http', 'ftp', 'plugin:/susecloud')
        for repo in repos_list:
            repo_path = os.sep.join(
                [repos_path, repo]
            )
            config.read(repo_path)
            repo_section = dict(config)
            for section in repo_section.keys():
                repo_info = dict(config.items(section))
                if repo_info:
                    if not repo_info['baseurl'].startswith(migration_accepted_prefixes):
                        if repo_info['baseurl'] not in no_remote_repos:
                            no_remote_repos.append(repo_info['baseurl'])

    if no_remote_repos:
        zypper_cmd = 'zypper repos --url'
        log.warning(
            'The following repositories may cause the migration to fail, as they '
            'may not be available during the migration:\n%s\nPlease, check those '
            'before starting the migration\nTo see all the repositories and '
            'their urls, you can run "%s"\n',
            '\n'.join(no_remote_repos), zypper_cmd,
        )
