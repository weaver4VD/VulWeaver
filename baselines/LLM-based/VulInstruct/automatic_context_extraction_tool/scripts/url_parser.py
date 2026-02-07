import re
import json
import subprocess
import os
from urllib.parse import urlparse
from typing import Dict, Tuple, Optional


class CommitURLParser:
    """Parse different formats of commit URLs and extract repository information"""
    
    def __init__(self):
        self.github_pattern = re.compile(
            r'https://github\.com/([^/]+)/([^/]+)/commit/([a-f0-9]+)'
        )
        self.gitweb_pattern = re.compile(
            r'https?://([^/]+)/\?p=([^;]+)\.git;a=commit(?:diff)?;h=([a-f0-9]+)'
        )
        self.cgit_pattern = re.compile(
            r'https?://([^/]+)/pub/scm/([^/]+/[^/]+/[^/]+)/([^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.kernel_cgit_pattern = re.compile(
            r'https?://git\.kernel\.org/pub/scm/linux/kernel/git/([^/]+)/([^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.cgit_simple_pattern = re.compile(
            r'https?://([^/]+)/([^/]+/[^/]+/[^/]+/[^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.direct_commit_pattern = re.compile(
            r'https?://([^/]+)/([^/]+)\.git/commit/([a-f0-9]+)'
        )
        self.gnome_pattern = re.compile(
            r'https?://([^/]+)/browse/([^/]+)/commit/\?id=([a-f0-9]+)'
        )
        self.gitlab_pattern = re.compile(
            r'https://([^/]+)/([^/]+)/([^/]+)/(?:-/)?commit/([a-f0-9]+)'
        )
        self.gitlab_mr_pattern = re.compile(
            r'https://([^/]+)/([^/]+)/([^/]+)/-/merge_requests/\d+/diffs\?commit_id=([a-f0-9]+)'
        )
        self.cgit_generic_pattern = re.compile(
            r'https?://([^/]+)/(?:cgit/)?([^/]+/[^/]+/[^/]+/[^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.kernel_cgit_alt_pattern = re.compile(
            r'https?://git\.kernel\.org/cgit/linux/kernel/git/([^/]+)/([^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.gitweb_commitdiff_pattern = re.compile(
            r'https?://([^/]+)/([^/]+)\.git/commitdiff/([a-f0-9]+)'
        )
        self.direct_git_commit_pattern = re.compile(
            r'https?://([^/]+)/([^/]+)\.git/commit/([a-f0-9]+)'
        )
        self.openldap_pattern = re.compile(
            r'https://git\.openldap\.org/([^/]+)/([^/]+)/-/commit/([a-f0-9]+)'
        )
        self.lysator_pattern = re.compile(
            r'https://git\.lysator\.liu\.se/([^/]+)/([^/]+)/commit/([a-f0-9]+)'
        )
        self.bitbucket_pattern = re.compile(
            r'https://bitbucket\.org/([^/]+)/([^/]+)/commits/([a-f0-9]+)'
        )
        self.savannah_cgit_pattern = re.compile(
            r'https?://git\.savannah\.gnu\.org/cgit/([^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.sv_gnu_cgit_pattern = re.compile(
            r'https?://git\.sv\.gnu\.org/cgit/([^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.clamav_gitweb_pattern = re.compile(
            r'https?://git\.clamav\.net/gitweb\?p=([^;]+)\.git;a=commit;h=([a-f0-9]+)'
        )
        self.libssh_project_pattern = re.compile(
            r'https?://git\.libssh\.org/projects/([^/]+)\.git/commit/\?(?:[^&]*&)*id=([a-f0-9]+)'
        )
        self.openssl_gitweb_pattern = re.compile(
            r'https?://git\.openssl\.org/gitweb/\?p=([^;]+)\.git;a=commit(?:diff)?;h=([a-f0-9]+)'
        )

    def parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub URL"""
        match = self.github_pattern.match(url)
        if match:
            owner, repo, commit_hash = match.groups()
            return {
                'type': 'github',
                'owner': owner,
                'repo': repo,
                'commit_hash': commit_hash,
                'clone_url': f'https://github.com/{owner}/{repo}.git',
                'repo_name': repo
            }
        return None

    def parse_gitweb_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Git web interface URL"""
        match = self.gitweb_pattern.match(url)
        if match:
            host, repo_path, commit_hash = match.groups()
            repo_name = repo_path.split('/')[-1]
            if 'kernel.org' in host:
                clone_url = f'https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git'
                repo_name = 'linux'
            elif 'php.net' in host:
                clone_url = f'https://github.com/php/php-src.git'
                repo_name = 'php-src'
            elif 'qemu.org' in host:
                clone_url = f'https://github.com/qemu/qemu.git'
                repo_name = 'qemu'
            elif 'ghostscript.com' in host:
                clone_url = f'https://github.com/ArtifexSoftware/ghostpdl.git'
                repo_name = 'ghostpdl'
            elif 'exim.org' in host:
                clone_url = f'https://github.com/Exim/exim.git'
                repo_name = 'exim'
            elif 'clamav.net' in host:
                clone_url = f'https://github.com/Cisco-Talos/clamav.git'
                repo_name = 'clamav'
            elif 'gnome.org' in host:
                clone_url = f'https://github.com/GNOME/gdk-pixbuf.git'
                repo_name = 'gdk-pixbuf'
            elif 'libssh.org' in host:
                clone_url = f'https://github.com/libssh/libssh.git'
                repo_name = 'libssh'
            else:
                clone_url = f'https://{host}/{repo_path}.git'
                
            return {
                'type': 'gitweb',
                'host': host,
                'repo_path': repo_path,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_cgit_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse CGit format URL"""
        match = self.cgit_pattern.match(url)
        if match:
            host, repo_path, repo_name, commit_hash = match.groups()
            if 'kernel.org' in host:
                if 'torvalds/linux' in repo_path:
                    clone_url = 'https://github.com/torvalds/linux.git'
                    repo_name = 'linux'
                else:
                    clone_url = f'https://github.com/torvalds/linux.git'
                    repo_name = 'linux'
            else:
                clone_url = f'https://{host}/pub/scm/{repo_path}/{repo_name}.git'
                
            return {
                'type': 'cgit',
                'host': host,
                'repo_path': repo_path,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        match = self.cgit_simple_pattern.match(url)
        if match:
            host, repo_path, commit_hash = match.groups()
            repo_name = repo_path.split('/')[-1]
            
            if 'kernel.org' in host:
                clone_url = 'https://github.com/torvalds/linux.git'
                repo_name = 'linux'
            else:
                clone_url = f'https://{host}/{repo_path}.git'
                
            return {
                'type': 'cgit_simple',
                'host': host,
                'repo_path': repo_path,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_direct_commit_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse direct commit URL format"""
        match = self.direct_commit_pattern.match(url)
        if match:
            host, repo_path, commit_hash = match.groups()
            repo_name = repo_path.split('/')[-1]
            if 'exim.org' in host:
                clone_url = 'https://github.com/Exim/exim.git'
                repo_name = 'exim'
            else:
                clone_url = f'https://{host}/{repo_path}.git'
                
            return {
                'type': 'direct_commit',
                'host': host,
                'repo_path': repo_path,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_gnome_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GNOME browse format URL"""
        match = self.gnome_pattern.match(url)
        if match:
            host, repo_name, commit_hash = match.groups()
            clone_url = f'https://github.com/GNOME/{repo_name}.git'
                
            return {
                'type': 'gnome',
                'host': host,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_gitlab_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitLab format URL"""
        mr_match = self.gitlab_mr_pattern.match(url)
        if mr_match:
            host, group, repo_name, commit_hash = mr_match.groups()
            if 'gitlab.com' in host:
                clone_url = f'https://gitlab.com/{group}/{repo_name}.git'
            elif 'gitlab.freedesktop.org' in host:
                if repo_name == 'cairo':
                    clone_url = 'https://github.com/freedesktop/cairo.git'
                else:
                    clone_url = f'https://gitlab.freedesktop.org/{group}/{repo_name}.git'
            else:
                clone_url = f'https://{host}/{group}/{repo_name}.git'
                
            return {
                'type': 'gitlab_mr',
                'host': host,
                'group': group,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
            
        match = self.gitlab_pattern.match(url)
        if match:
            host, group, repo_name, commit_hash = match.groups()
            if 'gitlab.com' in host:
                if group == 'gnutls' and repo_name == 'gnutls':
                    clone_url = 'https://github.com/gnutls/gnutls.git'
                else:
                    clone_url = f'https://gitlab.com/{group}/{repo_name}.git'
            elif 'gitlab.freedesktop.org' in host:
                if repo_name == 'poppler':
                    clone_url = 'https://github.com/freedesktop/poppler.git'
                elif repo_name == 'cairo':
                    clone_url = 'https://github.com/freedesktop/cairo.git'
                else:
                    clone_url = f'https://gitlab.freedesktop.org/{group}/{repo_name}.git'
            else:
                clone_url = f'https://{host}/{group}/{repo_name}.git'
                
            return {
                'type': 'gitlab',
                'host': host,
                'group': group,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_kernel_cgit_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Kernel.org CGit format URL"""
        match = self.kernel_cgit_pattern.match(url)
        if match:
            maintainer, project, commit_hash = match.groups()
            clone_url = 'https://github.com/torvalds/linux.git'
            repo_name = 'linux'
                
            return {
                'type': 'kernel_cgit',
                'host': 'git.kernel.org',
                'maintainer': maintainer,
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_kernel_cgit_alt_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Kernel.org alternative CGit format URL"""
        match = self.kernel_cgit_alt_pattern.match(url)
        if match:
            maintainer, project, commit_hash = match.groups()
            clone_url = 'https://github.com/torvalds/linux.git'
            repo_name = 'linux'
                
            return {
                'type': 'kernel_cgit_alt',
                'host': 'git.kernel.org',
                'maintainer': maintainer,
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_cgit_generic_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse generic CGit format URL"""
        match = self.cgit_generic_pattern.match(url)
        if match:
            host, repo_path, repo_name, commit_hash = match.groups()
            
            if 'kernel.org' in host:
                clone_url = 'https://github.com/torvalds/linux.git'
                repo_name = 'linux'
            else:
                clone_url = f'https://{host}/cgit/{repo_path}/{repo_name}.git'
                
            return {
                'type': 'cgit_generic',
                'host': host,
                'repo_path': repo_path,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_gitweb_commitdiff_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Gitweb commitdiff format URL"""
        match = self.gitweb_commitdiff_pattern.match(url)
        if match:
            host, repo_path, commit_hash = match.groups()
            repo_name = repo_path.split('/')[-1]
            if 'torproject.org' in host:
                clone_url = 'https://github.com/torproject/tor.git'
                repo_name = 'tor'
            else:
                clone_url = f'https://{host}/{repo_path}.git'
                
            return {
                'type': 'gitweb_commitdiff',
                'host': host,
                'repo_path': repo_path,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_direct_git_commit_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse direct Git repository commit format URL"""
        match = self.direct_git_commit_pattern.match(url)
        if match:
            host, repo_path, commit_hash = match.groups()
            repo_name = repo_path.split('/')[-1]
            if 'exim.org' in host:
                clone_url = 'https://github.com/Exim/exim.git'
                repo_name = 'exim'
            else:
                clone_url = f'https://{host}/{repo_path}.git'
                
            return {
                'type': 'direct_git_commit',
                'host': host,
                'repo_path': repo_path, 
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_openldap_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse OpenLDAP GitLab format URL"""
        match = self.openldap_pattern.match(url)
        if match:
            group, repo_name, commit_hash = match.groups()
            
            return {
                'type': 'openldap',
                'host': 'git.openldap.org',
                'group': group,
                'commit_hash': commit_hash,
                'clone_url': f'https://github.com/openldap/openldap.git',
                'repo_name': 'openldap'
            }
        
        return None

    def parse_lysator_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Lysator Git format URL"""
        match = self.lysator_pattern.match(url)
        if match:
            group, repo_name, commit_hash = match.groups()
            if repo_name == 'nettle':
                clone_url = 'https://github.com/gnutls/nettle.git'
            else:
                clone_url = f'https://git.lysator.liu.se/{group}/{repo_name}.git'
                
            return {
                'type': 'lysator',
                'host': 'git.lysator.liu.se',
                'group': group,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_bitbucket_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Bitbucket format URL"""
        match = self.bitbucket_pattern.match(url)
        if match:
            owner, repo_name, commit_hash = match.groups()
            if repo_name == 'monit':
                clone_url = 'https://github.com/tildeslash/monit.git'
            else:
                clone_url = f'https://github.com/{owner}/{repo_name}.git'
                
            return {
                'type': 'bitbucket',
                'host': 'bitbucket.org',
                'owner': owner,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_savannah_cgit_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GNU Savannah CGit format URL"""
        match = self.savannah_cgit_pattern.match(url)
        if match:
            project, commit_hash = match.groups()
            project_mapping = {
                'gnulib': 'https://github.com/coreutils/gnulib.git',
                'gzip': 'https://github.com/gnu/gzip.git',
                'tar': 'https://github.com/gnu/tar.git',
                'guile': 'https://github.com/gnu/guile.git'
            }
            
            clone_url = project_mapping.get(project, f'https://github.com/gnu/{project}.git')
                
            return {
                'type': 'savannah_cgit',
                'host': 'git.savannah.gnu.org',
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': project
            }
        
        return None

    def parse_sv_gnu_cgit_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GNU sv.gnu.org CGit format URL"""
        match = self.sv_gnu_cgit_pattern.match(url)
        if match:
            project, commit_hash = match.groups()
            if project == 'grep':
                clone_url = 'https://github.com/gnu/grep.git'
            else:
                clone_url = f'https://github.com/gnu/{project}.git'
                
            return {
                'type': 'sv_gnu_cgit',
                'host': 'git.sv.gnu.org',
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': project
            }
        
        return None

    def parse_clamav_gitweb_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse ClamAV Gitweb format URL"""
        match = self.clamav_gitweb_pattern.match(url)
        if match:
            project, commit_hash = match.groups()
            clone_url = 'https://github.com/Cisco-Talos/clamav.git'
            repo_name = 'clamav'
                
            return {
                'type': 'clamav_gitweb',
                'host': 'git.clamav.net',
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_libssh_project_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse LibSSH Project format URL"""
        match = self.libssh_project_pattern.match(url)
        if match:
            project, commit_hash = match.groups()
            clone_url = 'https://github.com/libssh/libssh.git'
            repo_name = 'libssh'
                
            return {
                'type': 'libssh_project',
                'host': 'git.libssh.org',
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_openssl_gitweb_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse OpenSSL Gitweb format URL"""
        match = self.openssl_gitweb_pattern.match(url)
        if match:
            project, commit_hash = match.groups()
            clone_url = 'https://github.com/openssl/openssl.git'
            repo_name = 'openssl'
                
            return {
                'type': 'openssl_gitweb',
                'host': 'git.openssl.org',
                'project': project,
                'commit_hash': commit_hash,
                'clone_url': clone_url,
                'repo_name': repo_name
            }
        
        return None

    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse commit URL of any format"""
        result = self.parse_github_url(url)
        if result:
            return result
        result = self.parse_gitlab_url(url)
        if result:
            return result
        result = self.parse_gitweb_url(url)
        if result:
            return result
        result = self.parse_cgit_url(url)
        if result:
            return result
        result = self.parse_kernel_cgit_url(url)
        if result:
            return result
        result = self.parse_kernel_cgit_alt_url(url)
        if result:
            return result
        result = self.parse_cgit_generic_url(url)
        if result:
            return result
        result = self.parse_direct_commit_url(url)
        if result:
            return result
        result = self.parse_gnome_url(url)
        if result:
            return result
        result = self.parse_gitweb_commitdiff_url(url)
        if result:
            return result
        result = self.parse_direct_git_commit_url(url)
        if result:
            return result
        result = self.parse_openldap_url(url)
        if result:
            return result
        result = self.parse_lysator_url(url)
        if result:
            return result
        result = self.parse_bitbucket_url(url)
        if result:
            return result
        result = self.parse_savannah_cgit_url(url)
        if result:
            return result
        result = self.parse_sv_gnu_cgit_url(url)
        if result:
            return result
        result = self.parse_clamav_gitweb_url(url)
        if result:
            return result
        result = self.parse_libssh_project_url(url)
        if result:
            return result
        result = self.parse_openssl_gitweb_url(url)
        if result:
            return result
            
        return None


def extract_commit_urls(jsonl_file: str) -> Dict[str, str]:
    """Extract all commit URLs from JSONL file"""
    urls = {}
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            try:
                data = json.loads(line)
                if 'commit_url' in data:
                    urls[line_no] = data['commit_url']
            except json.JSONDecodeError as e:
                print(f"JSON parsing error on line {line_no}: {e}")
    return urls


def clone_repository(repo_info: Dict[str, str], projects_dir: str = "../projects") -> bool:
    """Clone repository to specified directory"""
    repo_path = os.path.join(projects_dir, repo_info['repo_name'])
    if os.path.exists(repo_path):
        print(f"Repository {repo_info['repo_name']} already exists, skipping clone")
        return True
    os.makedirs(projects_dir, exist_ok=True)
    
    try:
        print(f"Cloning {repo_info['clone_url']} to {repo_path}")
        subprocess.run([
            'git', 'clone', '--depth', '50', repo_info['clone_url'], repo_path
        ], check=True, capture_output=True, text=True)
        
        print(f"Successfully cloned repository: {repo_info['repo_name']}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository {repo_info['repo_name']}: {e}")
        print(f"Error output: {e.stderr}")
        return False


if __name__ == "__main__":
    parser = CommitURLParser()
    
    test_urls = [
        "https://github.com/ImageMagick/ImageMagick6/commit/dc070da861a015d3c97488fdcca6063b44d47a7b",
        "http://git.qemu.org/?p=qemu.git;a=commit;h=9302e863aa8baa5d932fc078967050c055fa1a7f",
        "http://git.kernel.org/?p=linux/kernel/git/torvalds/linux-2.6.git;a=commit;h=649f1ee6c705aab644035a7998d7b574193a598a"
    ]
    
    for url in test_urls:
        result = parser.parse_url(url)
        print(f"URL: {url}")
        print(f"Parse result: {result}")
        print("-" * 80)

