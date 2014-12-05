from django.contrib.auth.models import User
from django.db.models.loading import get_model

from celery import task
from celery.utils.log import get_task_logger
from django.conf import settings
import facepy

logger = get_task_logger(__name__)


@task()
def create_and_send_action(user, url, content_id, action_name, object_name,
                           action_logging_model,
                           additional_action_kwargs={}):
    deprected = False
    if isinstance(user, int):
        user = User.objects.get(id=user)
    else:
        deprected = True
    if isinstance(action_logging_model, list) or isinstance(action_logging_model, tuple):
        action_logging_model = get_model(*action_logging_model)
    else:
        deprected = True

    if deprected:
        logger.warning('Deprected create_and_send_action args types')

    action = OpengraphAction(user, url, content_id, action_name, object_name, action_logging_model,
                             additional_action_kwargs)
    action.run()


class OpengraphAction(object):
    def __init__(self, user, url, content_id, action_name, object_name, action_logging_model,
                 additional_action_kwargs={}):
        self.user = user
        self.url = url
        self.content_id = content_id
        self.action_name = action_name
        self.object_name = object_name
        self.action_logging_model = action_logging_model
        self.metric_success_key = '%s_%s_success' % (self.object_name, self.action_name)
        self.metric_failure_key = '%s_%s_failure' % (self.object_name, self.action_name)
        self.USE_METRICS = getattr(settings, 'USE_METRICS', False)
        self.additional_action_kwargs = additional_action_kwargs

    def run(self):
        try:
            graph = self._get_graph()
        except AttributeError:
            pass
        else:
            self._create_action(graph)

    def _get_graph(self):
        return self.user.facebookuser.graph

    def _create_action(self, graph):
        url_kwarg = {self.object_name: self.url}
        kwargs = dict(url_kwarg, **self.additional_action_kwargs)
        action = self._get_action()
        try:
            response = graph.post('me/%s' % action, **kwargs)
        except (facepy.graph_api.GraphAPI.FacebookError, facepy.FacepyError) as e:
            self._log_errors(e)
            self._increment_failure_metric()
        else:
            try:
                response_id = response['id']
            except TypeError as e:
                self._log_errors(e)
                self._increment_failure_metric()
            else:
                self._save_successful_opengraph_action(long(response_id))
                self._increment_success_metric()

    def _increment_success_metric(self):
        if self.USE_METRICS:
            from redis_metrics import metric
            metric(self.metric_success_key, category="OpenGraphAction")

    def _increment_failure_metric(self):
        if self.USE_METRICS:
            from redis_metrics import metric
            metric(self.metric_failure_key, category="OpenGraphAction")

    def _get_action(self):
        if self.action_name.count('.') > 0:
            return self.action_name
        else:
            return '%s:%s' % (settings.FACEBOOK_APP_NAMESPACE, self.action_name)

    def _log_errors(self, e):
        code = getattr(e, 'code', None)
        message = "Creating %s:%s action - %s" % (self.object_name, self.action_name, e.message)
        low_priority_codes = self.low_priority_opengraph_errors().keys()
        if code in low_priority_codes:
            logger.warning(message)
        else:
            logger.exception(message)
        if code:
            self._save_action_error_code(code)

    def low_priority_opengraph_errors(self):
        return {
            1: 'An unknown error occurred',
            100: 'Invalid parameter / action not accepted',
            190: 'Invalid OAuth 2.0 Access Token',
            200: 'Permissions error',
            3501: 'Already liked object',
        }

    def _save_action_error_code(self, code):
        action = self._get_action_object()
        action.error_code = code
        action.save()

    def _get_action_object(self):
        kwargs = {
            'content_id': self.content_id,
            'user_id': self.user.id,
        }
        action, _ = self.action_logging_model.objects.get_or_create(**kwargs)
        return action

    def _save_successful_opengraph_action(self, action_id):
        action = self._get_action_object()
        action.facebook_action_id = action_id
        action.executed = True
        action.save()
