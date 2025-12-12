from odoo import http
from odoo.http import request

class AcuCareRedirect(http.Controller):

    @http.route('/', auth='public', website=True)
    def redirect_home(self):
        return request.redirect('/acucare-home')