# xblock-launchcontainer
Open edX XBlock to include Appsembler's external course Container launcher

v Installation

## FOR LOCAL DEVELOPMENT

*The easiest way to do local development is with the `xblock-sdk`.* 

### Step 1: Get the xblock-sdk

``` 
git clone git@github.com:edx/xblock-sdk.git
```

### Step 2: Set up a virtualenv (not virtualenvwrapper)

*Virtualenvwrapper doesn't allow the editable install process to work properly.* 

```
cd xblock-sdk
virtualenv .
```

### Step 3: Install this package in "editable mode"

Append this package to your `xblock-sdk/requirements/base.txt`:

``` 
-e git+https://github.com/appsembler/xblock-launchcontainer.git@master#egg=launchcontainer
```

Install the packages:

*Note: This command is more complex than necessary due to a bug in pip--but this is what we need to make it work.*

``` 
$ PYTHONPATH=$(pwd)/lib/python2.7/site-packages pip install --install-option="--prefix=$(pwd)" -r requirements/base.txt
```

### Step 4: Start the xblock-sdk server 

``` 
python manage.py migrate
python manage.py runserver 8002  # Use 8002 b/c devstack will take 8000 and 8001
```

You should now see a "Single Launchcontainer" in the list of avaialable XBlocks:

*TODO: Add LC screenshot*

### Step 5: Set up the Wharf machine and configure the XBlock to talk to it

To make a request from the XBlock to Wharf, you should set up your local Wharf environment (instructions [here](https://github.com/appsembler/wharf/blob/develop/docs/index.md)). Then take the ip of the container running Wharf master server, and set environment variables that will tell the XBlock where to make the request. First, modify your `xblock-sdk/workbench/settings.py` to include this: 

``` 
ENV_TOKENS = {
    'LAUNCHCONTAINER_API_CONF': {
     'http://192.xxx.xx.xxx:8000/path/to/AVLContainerEndpoint/'
    }
}
```

*1. HOST should be the IP of the machine hosting your Wharf containers.*
*2. The PATH should be the path of the endpoint in Wharf that receives requests to deploy new containers.*

Start Django's dev server:

``` 
python manage.py runserver 8002
```

You should then be able to take the title and the token of a Wharf project, and plug it into the XBlock: 

*To find this view, append studio_view/ to any "scenario" url that the sdk generates.*

*TODO: Insert screenshot of sdk studio_view.*

## INSTALL FOR DEVSTACK DEVELOPMENT 

*Tested with Eucalyptus.*

### Install the launchcontainer source 

If you have devstack installed, you'll find a `src/` directory on your host, where we'll install the xblock: 

``` 
$ ls
Vagrantfile         ecommerce           edx-platform        programs            themes
cs_comments_service ecommerce-worker    lib                 src
```

To clone the repo using pip in editable mode, we're going to have to use virtualenv (not virtualenvwrapper): 

``` 
$ cd <devstackDir> 
$ virtualenv .
$ pip install --target=$(pwd)/lib/python2.7 -e git+https://github.com/appsembler/xblock-launchcontainer.git@master#egg=launchcontainer
```

A mirrored copy of the xblock will now be in the Vagrant machine's `/edx/src/` directory. Next you'll set up pip within the devstack to use the proper location: 

```
$ vagrant ssh 
$ sudo su edxapp
$ /edx/bin/pip.edxapp install -e git+https://github.com/appsembler/xblock-launchcontainer.git@master#egg=launchcontainer
```

Now we'll edit pips recent install to point to your source by updating the `/edx/app/edxapp/venvs/edxapp/lib/python2.7/site-packages/xblock-launchcontainer.egg-link` file to read as follows: 

```
/edx/src/launchcontainer
```

Next, you'll need to update the `/edx/app/edxapp/venvs/edxapp/lib/python2.7/site-packages/easy-install.pth` file to include `/edx/src/xblock-launchcontainer` amongst the several other packages listed there: 

```
...
/edx/app/edxapp/venvs/edxapp/src/rate-xblock
/edx/app/edxapp/venvs/edxapp/src/done-xblock
/edx/app/edxapp/venvs/edxapp/src/xblock-google-drive
/edx/src/launchcontainer
/edx/app/edxapp/venvs/edxapp/src/edx-reverification-block
/edx/app/edxapp/venvs/edxapp/src/edx-sga
/edx/app/edxapp/venvs/edxapp/src/xblock-poll
...
```

### Enable the XBlock in the devstack UI 

In Studio, navigate to a Course > 'Advanced Settings' > 'Advanced Module List' and add `launchcontainer` to the list.

### Set the env vars to point to your instance of Wharf

Update your `lms.env.json` and `cms.env.json` to include:

```
'LAUNCHCONTAINER_API_CONF': {
    'http://192.xxx.xx.xxx:8000/path/to/avlContainerEndpoint/'
}
```

Then restart your devstack studio, and you should be able to use the XBlock, making requests to your local instance of Wharf.

*WARNING: If you are logged in to Wharf in one tab, trying to make requests from the xblock-sdk web server, you'll likely see a 403, and a message that says you've submitted an incorrect token. This fails just because you have a `sessionid` in the other tab and the Wharf API is taking that and treating you like a staff user, who needs a CSRF token. It is hereby recommended that you use an incognito window for the xblock-sdk server and the edX studio server.*

## PRODUCTION INSTALL 

### Install the master branch of this repo with pip 

```
$ pip install -e git+https://github.com/appsembler/xblock-launchcontainer.git@master#egg=launchcontainer
```

or add to your requires.txt

```
-e git+https://github.com/jazkarta/xblock-launchcontainer.git@master#egg=launchcontainer
```

Update your `lms.env.json` and `cms.env.json` to add:

```
"ADDL_INSTALLED_APPS" : ["launchcontainer"]
```
and 

```
"FEATURES": {
    "ALLOW_ALL_ADVANCED_COMPONENTS": true
}
```

# Usage

* In Studio, navigate to a Course, and select 'Advanced Settings' underneath the 
'Settings' dropdown menu.
* Under  'Advanced Module List' add 
```
["launchcontainer"] to the list of advanced modules
```
* Return to the Course Outline
* Create a Section, Sub-section and Unit, if you haven’t already
* In the “Add New Component” interface, you should now see an “Advanced” button
* Click “Advanced” and choose “launchcontainer”
