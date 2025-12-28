from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied, ValidationError


class AcuCareController(http.Controller):

    # 1. Redirect Root to AcuCare Home
    @http.route('/', auth='public', website=True)
    def redirect_home(self):
        return request.redirect('/acucare-home')

    # 2. Render the Signup Page (Logic Removed)
    @http.route('/acucare/signup', type='http', auth='public', website=True)
    def signup_page(self, **kw):
        # Simply pass the raw error code (e.g., 'missing', 'password') to the template
        values = {
            'error_message': kw.get('error'),
        }
        return request.render('new_AcuCare_website.acucare_signup', values)

    @http.route('/acucare/signup/submit', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def signup_submit(self, **post):

        # 1. Get Form Data
        name = post.get('name', '').strip()
        login = post.get('login', '').strip()
        password = post.get('password', '')
        confirm = post.get('confirm_password', '')

        # 2. Validation
        if not all([name, login, password, confirm]):
            return request.redirect('/acucare/signup?error=missing')

        if password != confirm:
            return request.redirect('/acucare/signup?error=password')

        if len(password) < 6:
            return request.redirect('/acucare/signup?error=weak')

        # 3. Check if user already exists
        existing = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        if existing:
            return request.redirect('/acucare/signup?error=exists')

        # 4. Create User & Assign Groups (Odoo 19 Safe Logic)
        try:
            portal_group = request.env.ref('base.group_portal')
            technical_public_group = request.env.ref('website.website_page_controller_expose', raise_if_not_found=False)

            # Build Group List
            group_ids = [portal_group.id]
            if technical_public_group:
                group_ids.append(technical_public_group.id)
            # Step A: Create User
            user = request.env['res.users'].sudo().create({
                'name': name,
                'login': login,
                'email': login,
                'password': password,
                'active': True,
                'groups_id': [(6, 0, group_ids)],
            })


            # Step B: Manage Groups (Remove Internal, Add Portal)
            # We write to the GROUP model to avoid Odoo 19 errors
            internal_group = request.env.ref('base.group_user')
            portal_group = request.env.ref('base.group_portal')
            technical_public_group = request.env.ref('website.website_page_controller_expose', raise_if_not_found=False)

            # 1. Remove 'Internal User' group
            internal_group.sudo().write({'user_ids': [(3, user.id)]})

            # 2. Add 'Portal' group
            portal_group.sudo().write({'user_ids': [(4, user.id)]})

            # 3. Add 'Technical Public' group if it exists
            if technical_public_group:
                technical_public_group.sudo().write({'user_ids': [(4, user.id)]})

            # Step C: Commit Transaction (Crucial for login)
            request.env.cr.commit()

        except ValidationError as e:
            return request.redirect('/web/login?signup=success')
        except Exception as e:
            print(f"Signup Error: {e}")
            return request.redirect('/web/login?signup=success')

        # 5. Authenticate
        try:
            request.session.authenticate(request.env.cr.dbname, login=login, password=password)
        except Exception as e:
            print(f"Login failed: {e}")
            return request.redirect('/web/login?signup=success')

        # 6. Redirect to Home
        return request.redirect('/acucare-home')