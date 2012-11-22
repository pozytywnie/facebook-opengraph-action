facebook-opengraph-action
==================================

facebook-opengraph-action is a Django application that
manages Facebook OpenGraph actions - creation, sending via Celery and saving responses.

Installation
------------

Package
_______

facebook-opengraph-action can be installed as a normal Python package.

Example instalation for pip::

    $ pip install facebook-opengraph-action


Configuration
-------------

settings.py
___________

Add facebook_javascript_authentication to INSTALLED_APPS::

    INSTALLED_APPS = (
        ...
        'facebook_opengraph_action',
        ...
    )

Add "facebook_opengraph_action.opengraph_action", urls to CELERY_IMPORTS::

    CELERY_IMPORTS = (
        ...
        "facebook_opengraph_action.opengraph_action",
        ...
    )

You need to have Celery up and running to send actions to Facebook.


Usage
-------------

Creating a model for content
____________________________

You need to create a model that will store data about actions for given content entry (user and content ID plus other additional data).
Import the OpenGraphActionModel abstract model and inherit it in your model adding a "content" Foreign field to the content used by the action. For example:

from facebook_opengraph_action import models as opengraph_models

class FacebookPhotoLikeAction(opengraph_models.OpenGraphActionModel):
    content = models.ForeignKey('my_app.Photo')


Creating and sending OpenGraph action
_____________________________________

To create and send an action you need to call opengraph_action.create_and_send_action.delay() method passing all required arguments:

- user object
- absolute content (page) adress
- unique content id
- action name
- og:type name
- OpenGraphActionModel model class used for given opengraph action

Here is an example from a class based view:

    def _send_to_facebook(self):
        kwargs = {
            'content': self.object,
            'user': self.request.user,
        }
        if not models.FacebookLikeAction.objects.filter(**kwargs).exists():
            self._lock_actions_for_content(kwargs)
            opengraph_action.create_and_send_action.delay(
                self.request.user,
                self.object.get_absolute_address(),
                self.object.id,
                'og.likes',
                'object',
                models.FacebookPhotoLikeAction
            )


Things like action and og:type values you can get from the opengraph configuration of your Facebook app
(when you create an action there you can view example code showcasing those values). The content must have correct og:tags
under given absolute address (og:type !) or the action will return an error.

Each call to .delay() should create and start a cellery task. To see them localy start celeryd  as follows:

django-admin.py celeryd -l info
