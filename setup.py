from distutils.core import setup

setup(
    name='cobiv',
    version='0.1',
    packages=['cobiv', 'cobiv.libs', 'cobiv.test', 'cobiv.test.modules', 'cobiv.test.modules.browser',
              'cobiv.test.modules.session', 'cobiv.test.modules.sqlitedb', 'cobiv.test.modules.thumbloader',
              'cobiv.modules', 'cobiv.modules.io', 'cobiv.modules.io.reader', 'cobiv.modules.io.tag-crc',
              'cobiv.modules.core', 'cobiv.modules.core.session', 'cobiv.modules.core.imageset',
              'cobiv.modules.core.thumbloader', 'cobiv.modules.views', 'cobiv.modules.views.help',
              'cobiv.modules.views.viewer', 'cobiv.modules.views.browser', 'cobiv.modules.database',
              'cobiv.modules.database.sqlitedb', 'cobiv.modules.hud_components', 'cobiv.modules.hud_components.sidebar',
              'cobiv.modules.hud_components.sidebar.widgets', 'cobiv.modules.hud_components.progresshud'],
    url='https://github.com/gokudomatic/cobiv',
    license='MIT',
    author='gokudomatic',
    author_email='gourry.gabrief@gmail.com',
    description='COmmand Based Image Viewer'
)
