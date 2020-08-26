$PROJECT = 'bluesky_scanplans'
$ACTIVITIES = [
    'version_bump',
    'changelog',
    'tag',
    'push_tag',
    'ghrelease',
    'pypi',
]

$VERSION_BUMP_PATTERNS = [
    ('scanplans/__init__.py', '__version__\s*=.*', "__version__ = '$VERSION'"),
    ('setup.py', 'version\s*=.*,', "version='$VERSION',")
]

$CHANGELOG_FILENAME = 'CHANGELOG.rst'
$CHANGELOG_TEMPLATE = 'TEMPLATE.rst'
$TAG_REMOTE = 'git@github.com:Billingegroup/bluesky_scanplans.git'

$GITHUB_ORG = 'BillingeGroup'
$GITHUB_REPO = 'bluesky_scanplans'
