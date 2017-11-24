"""Top-level handler code"""
import os
import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb
from models import CheckListItem, Note

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

        self._create_note(user)

        logout_url = users.create_logout_url(self.request.uri)

        template_context = {
            'user': user.nickname(),
            'logout_url': logout_url
        }

        self.response.write(self._render_template("main.html", template_context))

    @ndb.transactional
    def _create_note(self, user):
        note = Note(parent = ndb.Key("User", user.nickname()),
            title = self.request.get('title'),
            content = self.request.get('content'))
        
        note.put()

        item_titles = self.request.get("checklist_items").split(",")

        for item_title in item_titles:
            item = CheckListItem(parent=note.key, title=item_title)
            item.put()
            note.checklist_items.append(item.key)
        
        note.put()


    def _render_template(self, template_name, context=None):
        if context is None:
            context = {}

        user = users.get_current_user()
        key = ndb.Key("User", user.nickname())
        qry = Note.owner_query(key)
        context['notes'] = qry.fetch()

        template = jinja_env.get_template(template_name)
        return template.render(context)



app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)