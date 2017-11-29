"""Top-level handler code"""
import os
import mimetypes
import jinja2
import webapp2
import cloudstorage

from google.appengine.api import app_identity, users
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

        bucket_name = app_identity.get_default_gcs_bucket_name()
        
        uploaded_file = self.request.POST.get('uploaded_file')
        file_name = getattr(uploaded_file, "filename", None)
        file_content = getattr(uploaded_file, "file", None)

        import pdb; pdb.set_trace()

        real_path = ""

        if file_name and file_content:
            content_t = mimetypes.guess_type(file_name)[0]
            real_path = os.path.join("/", bucket_name, user.user_id(), file_name).replace("\\","/")

            # import pdb; pdb.set_trace();

            with cloudstorage.open(real_path, "w", content_type=content_t) as f:
                f.write(file_content.read())

        self._create_note(user, file_name)

        logout_url = users.create_logout_url(self.request.uri)

        template_context = {
            'user': user.nickname(),
            'logout_url': logout_url
        }

        self.response.write(self._render_template("main.html", template_context))

    @ndb.transactional
    def _create_note(self, user, file_name):
        note = Note(parent = ndb.Key("User", user.nickname()),
            title = self.request.get('title'),
            content = self.request.get('content'))
        
        note.put()

        # added filter to the following line to remove any empty checklist items
        # item_titles = self.request.get("checklist_items").split(",")
        item_titles = filter(None, self.request.get("checklist_items").split(","))

        for item_title in item_titles:
            item = CheckListItem(parent=note.key, title=item_title)
            item.put()
            note.checklist_items.append(item.key)
        
        if file_name:
            note.files.append(file_name)

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


class MediaHandler(webapp2.RequestHandler):
    def get(self, file_name):
        user = users.get_current_user()

        bucket_name = app_identity.get_default_gcs_bucket_name()
        content_t = mimetypes.guess_type(file_name)[0]

        real_path = os.path.join("/", bucket_name, user.user_id(), file_name).replace("\\","/")

        try:
            with cloudstorage.open(real_path, 'r') as f:
                self.response.headers.add_header("Content-Type", content_t)
                self.response.out.write(f.read())

        except cloudstorage.errors.NotFoundError:
            self.abort(404)


app = webapp2.WSGIApplication([
    (r'/', MainHandler),
    (r'/media/(?P<file_name>[\w.]{0,256})', MediaHandler)
], debug=True)