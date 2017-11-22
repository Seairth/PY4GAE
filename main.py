"""Top-level handler code"""
import os
import webapp2
import jinja2

from google.appengine.api import users

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class MainHandler(webapp2.RequestHandler):
    """This is the handler class"""

    def get(self):
        """Main GET handler"""

        user = users.get_current_user()

        if user is not None:
            logout_url = users.create_logout_url(self.request.url)
            template_context = {
                'user': user.nickname(),
                'logout_url': logout_url
            }

            self.response.write(self._render_template("main.html", template_context))
        else:
            login_url = users.create_login_url(self.request.uri)
            self.redirect(login_url)

    def post(self):
        """Handles for request(s)"""

        user = users.get_current_user()

        if user is None:
            self.error(401)

        logout_url = users.create_logout_url(self.request.uri)

        template_context = {
            'user': user.nickname(),
            'logout_url': logout_url,
            'note_title': self.request.get('title'),
            'note_content': self.request.get('content')
        }

        self.response.write(self._render_template("main.html", template_context))

    def _render_template(self, template_name, context=None):
        if context is None:
            context = {}

        template = jinja_env.get_template(template_name)
        return template.render(context)



app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)