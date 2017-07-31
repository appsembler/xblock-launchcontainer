# xblock-launchcontainer

Open edX XBlock to launch containers from Appsembler's Virtual Labs (Wharf).

# Requirements 

This needs to run in one of two environments: the `xblock-sdk` or within Open edX. It has been tested with Dogwood, Eucalyptus, and Fikus. The only library required (besides, of course `xblock` is `django-crum`. I suspect your instance of Open edX already has both of these installed.

# Installation

## FOR LOCAL DEVELOPMENT w/ xblock-sdk

*You can do some of the local dev tasks with the xblock-sdk. Go this route if you're not concerned with styling.*

### Get the xblock-sdk

``` 
git clone git@github.com:edx/xblock-sdk.git
```

### Set up a virtualenv (not virtualenvwrapper)

*Virtualenvwrapper doesn't allow the editable install process to work properly.* 

```
cd xblock-sdk
virtualenv .
```

#### Update the version of XBlock 

The sdk probably has a version of XBlock that is ahead of us. Check setup.py 
to see what version we're on, then edit the xblock-sdk's `requirements/base.txt` to 
match. Then go run setup.py in the `xblock-sdk` directory: 

``` 
python setup.py develop
```

### Install this package in "editable mode"

Append this package to your `xblock-sdk/requirements/base.txt`:

``` 
-e git+https://github.com/appsembler/xblock-launchcontainer.git@develop#egg=launchcontainer
```

Install the packages:

*Note: This command is more complex than necessary due to a bug in pip--but this is what we need to make it work.*

``` 
$ PYTHONPATH=$(pwd)/lib/python2.7/site-packages pip install --install-option="--prefix=$(pwd)" -r requirements/base.txt
```

### Start the xblock-sdk server 

``` 
python manage.py migrate
python manage.py runserver 8002  # Use 8002 b/c devstack will take 8000 and 8001
```

You should now see a "Single Launchcontainer" in the list of avaialable XBlocks:

*TODO: Add LC screenshot*

### Set up the Wharf machine and configure the XBlock to talk to it

To make a request from the XBlock to Wharf, you should set up your local Wharf environment (instructions [here](https://github.com/appsembler/wharf/blob/develop/docs/index.md)). Then take the ip of the container running Wharf master server, and set environment variables that will tell the XBlock where to make the request. First, modify your `xblock-sdk/workbench/settings.py` to include this: 

``` 
ENV_TOKENS = {
    'LAUNCHCONTAINER_WHARF_URL': 'http://192.xxx.xx.xxx:8000/path/to/endpoint/' 
}
```

Start Django's dev server:

``` 
python manage.py runserver 8002  # edX takes 8000 and 8001.
```

You should then be able to take the title and the token of a Wharf project, and plug it into the XBlock: 

*To find this view, append studio_view/ to any "scenario" url that the sdk generates.*

*TODO: Insert screenshot of sdk studio_view.*

TODO: How to run the tests, including adding django.contrib.site. This should be in the dependencies, too.

## INSTALL FOR DEVSTACK DEVELOPMENT 

*Tested with Eucalyptus.*

### Install the launchcontainer source 

If you have devstack installed, you'll find a `src/` directory on your host, where we'll install the XBlock: 

``` 
$ ls
Vagrantfile         ecommerce           edx-platform        programs            themes
cs_comments_service ecommerce-worker    lib                 src
```

To clone the repo using pip in editable mode, we're going to have to use virtualenv (not virtualenvwrapper): 

``` 
$ cd <devstackDir> 
$ virtualenv .
$ pip install --target=$(pwd)/lib/python2.7 -e git+https://github.com/appsembler/xblock-launchcontainer.git@develop#egg=launchcontainer
```

A mirrored copy of the xblock will now be in the Vagrant machine's `/edx/src/` directory. Next you'll tell pip (in devstack) to use your synced location: 

```
$ vagrant ssh 
$ sudo su edxapp
$ /edx/bin/pip.edxapp install -e git+https://github.com/appsembler/xblock-launchcontainer.git@develop#egg=launchcontainer
```

Now we'll edit pip's recent install to point to your source by updating the `/edx/app/edxapp/venvs/edxapp/lib/python2.7/site-packages/xblock-launchcontainer.egg-link` file to read as follows: 

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

In Studio, navigate to a course > 'Advanced Settings' > 'Advanced Module List' and add `launchcontainer` to the list.

### Set the env vars to point to your instance of Wharf

*Note: This is not the preferred mode of configuration, but is supported. Please use the SiteConfiguration option below and see the section on variable precedence.*

To use this option, your `ENV_TOKENS` need to include this variable:

```
'LAUNCHCONTAINER_WHARF_URL': 'http://192.xxx.xx.xxx:8000/path/to/avlContainerEndpoint/'
```

### Make edX aware of this app / XBlock

Extend your `ENV_TOKENS` in the `devstack_appsembler.py` settings module: 

```
ENV_TOKENS.update({"ADDL_INSTALLED_APPS" : ["launchcontainer"]})
```

and: 

```
ENV_TOKENS["FEATURES"].update({"ALLOW_ALL_ADVANCED_COMPONENTS": true}) 
``` 

Then restart devstack studio, and you should be able to use the XBlock, making requests to your local instance of Wharf. Proceed to the "Usage" section below for more details on using the interface. 

!!! warning 

    If you are logged in to Wharf in one tab, trying to make requests from the xblock-sdk web server, you'll likely see a 403, and a message that says you've submitted an incorrect token. This fails just because you have a `sessionid` cookie in the other tab and the Wharf API is taking that and treating you like a staff user, who needs a CSRF token. We recommended using an incognito window for the xblock-sdk server and the edX studio server.*

### Preferred setting: Use the SiteConfiguration App

edX extends the Django site framework to include more configuration options. To modify the endpoint, navigate to the Django Admin within Studio, and add the following to the `Values` field of the SiteConfiguration object associated with your Site:

```
'LAUNCHCONTAINER_WHARF_URL': 'http://192.xxx.xx.xxx:8000/path/to/avlContainerEndpoint/'
```

### Add some logging 

XBlock launchcontainer will write debug level logs to `launchcontainer.launchcontainer`. Here is an example configuration that may be added to your `devstack_appsembler.py` settings file:

```
LOGGING['loggers'].update({
    'launchcontainer.launchcontainer': {
        'handlers': ['console', 'local'],
        'level': 'DEBUG',
        'propagate': True
        },
})

LOGGING['handlers']['console']['level'] = 'DEBUG'
```

## PRODUCTION INSTALL 

### Install the master branch of this repo with pip 

```
$ vagrant ssh 
$ sudo su edxapp
$ /edx/bin/pip.edxapp install git+https://github.com/appsembler/xblock-launchcontainer.git@master#egg=launchcontainer
```

Extend your `ENV_TOKENS` in the `devstack_appsembler.py` settings module: 

```
ENV_TOKENS.update({"ADDL_INSTALLED_APPS" : ["launchcontainer"]})
```

and: 

```
ENV_TOKENS["FEATURES"].update({"ALLOW_ALL_ADVANCED_COMPONENTS": true}) 
``` 

## USAGE

* In Studio, navigate to a Course, and select 'Advanced Settings' underneath the 
'Settings' dropdown menu.
* Under  'Advanced Module List' add `["launchcontainer"]` to the list of advanced modules
* Return to the Course Outline
* Create a Section, Sub-section and Unit, if you haven’t already
* In the “Add New Component” interface, you should now see an “Advanced” button
* Click “Advanced” and choose “Container Launcher"
* Get a project name and token from Wharf, entering them into the appropriate fields 

*The [Open edX documentation on XBlock][xblock-usage] usage may also prove useful at this step.*

## CONFIGURATION AND VARIABLE PRECEDENCE

You will always have an AVL cluster associated with this XBlock. It can be set in several ways, with the preferred method being the `SiteConfiguration` via the Django sites framework. You can also configure an instance-wide (i.e., across the entire edX instance) by setting an edX environment variable of `LAUNCHCONTAINER_WHARF_URL=http://your.url.com/your/endpoint/`, such that it will be available in `ENV_TOKENS['LAUNCHCONTAINER_WHARF_URL']`. 

The code will find your URL in the following order: 

1) The SiteConfiguration object associated with your Site: `SiteConfiguration().values['LAUNCHCONTAINER_WHARF_URL']` (str)   
2) The edX env var: `ENV_TOKENS['LAUNCHCONTAINER_WHARF_URL']` (str)  
3) \[Deprecated\]: `ENV_TOKENS['LAUNCHCONTAINER_API_CONF']['default']` (str)  
4) Fall back to the value defined in `launchcontainer.py`

*Note: This variable is cached, and the cache will be updated when the `SiteConfiguration` is changed.*

# Testing

To run the browser tests, execute these commands: 

``` 
$ pip install -r requirements/local.txt
$ cd launchcontainer
$ python -m unittest -v test_module
```

To run the Python unit tests, you'll need the xblock-sdk. If you followed the steps above to install it, you should be able to run `python manage.py test` from the root of your xblock-sdk.

[xblock-usage]: http://edx.readthedocs.io/projects/xblock-tutorial/en/latest/edx_platform/devstack.html
