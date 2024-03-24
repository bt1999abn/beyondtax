from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # reformat the response
        response = renderer_context['response']
        final_response = {
            "status_code": response.status_code,
            "status_text": response.status_text
        }
        key = "error" if response.exception else "data"
        final_response[key] = response.data
        # call super to render the response
        return super(CustomJSONRenderer, self).render(
           final_response, accepted_media_type, renderer_context
        )
