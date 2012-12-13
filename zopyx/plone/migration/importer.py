################################################################
# Poor men's Plone export
# (C) 2012, ZOPYX Ltd, D-72074 Tuebingen
################################################################

import os
import shutil
import tempfile
import glob
import transaction
from datetime import datetime
from ConfigParser import ConfigParser
from Products.CMFPlone.factory import addPloneSite
from Products.CMFPlone.utils import _createObjectByType
from Testing.makerequest import makerequest
from optparse import OptionParser
from AccessControl.SecurityManagement import newSecurityManager


def import_members(plone, import_dir, verbose):

    print 'Importing members'

    pr = plone.portal_registration
    pm = plone.portal_membership

    members_ini = os.path.join(import_dir, 'members.ini')

    CP = ConfigParser()
    CP.read([members_ini])
    get = CP.get

    for section in CP.sections():
        username = get(section, 'username')
        if verbose:
            print '-> %s' % username

        # omit group accounts
        if username.startswith('group_'):
            continue

        try:
            pr.addMember(username, get(section, 'password'))
        except:
            print '-> ERROR: omitting %s' % username
            continue
        member = pm.getMemberById(username)
        pm.createMemberArea(username)
        member.setMemberProperties(dict(email=get(section, 'email'),
                                        fullname=get(section, 'fullname'),
                                  ))


def log(s):
    print >>sys.stdout, s

def setup_plone(app, site_id, products=(), profiles=()):
    app = makerequest(app)
    addPloneSite(app, site_id, create_userfolder=True, extension_ids=profiles)
    plone = app[site_id]
    qit = plone.portal_quickinstaller

    ids = [p['id'] for p in qit.listInstallableProducts(skipInstalled=1) ]
    for product in products:
        if product in ids:
            qit.installProduct(product)

    if 'front-page' in plone.objectIds():
        plone.manage_delObjects('front-page')
    return plone

def import_plone(app, options):

    if not os.path.exists(options.input_directory):
        raise ValueError('Input directory does not exist')

    site_id = options.input_directory.rsplit('/', 1)[-1]
    profiles = ['plonetheme.sunburst:default']
    if options.timestamp:
        site_id += '_' + datetime.now().strftime('%Y%m%d-%H%M%S')
    plone = setup_plone(app, site_id, profiles=profiles)
    return plone.absolute_url(1)

def import_site(options):

    uf = app.acl_users
    user = uf.getUser(options.username)
    if user is None:
        raise ValueError('Unknown user: %s' % options.username)
    newSecurityManager(None, user.__of__(uf))

    url = import_plone(app, options)
    log('Committing...')
    transaction.commit()
    log('done')
    log(url)


if __name__ == '__main__':


    parser = OptionParser()
    parser.add_option('-u', '--user', dest='username', default='admin')
    parser.add_option('-i', '--input', dest='input_directory', default='')
    parser.add_option('-t', '--timestamp', dest='timestamp', action='store_true')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False)

    options, args = parser.parse_args()
    import_site(options)


