import request_handler
import user_util
import util_badges
import user_models
import badges
import custom_badges
import models_badges


class CreateCustomBadge(request_handler.RequestHandler):
    @user_util.developer_required
    def get(self):
        template_values = {
                "badge_categories":
                    [(badge_id, badges.BadgeCategory.get_type_label(badge_id))
                     for badge_id in badges.BadgeCategory.empty_count_dict()],
                "failed": self.request_bool("failed", default=False),
                }

        self.render_jinja2_template("badges/create_custom_badge.html",
                                    template_values)

    @user_util.developer_required
    def post(self):
        name = self.request_string("name")
        description = self.request_string("description")
        full_description = self.request_string("full_description")
        points = self.request_int("points", default=-1)
        badge_category = self.request_int("badge_category", default=-1)
        icon_src = self.request_string("icon_src", default="")

        # Create custom badge
        badge = models_badges.CustomBadgeType.insert(name, description,
            full_description, points, badge_category, icon_src)
        if badge:
            util_badges.all_badges(bust_cache=True)
            util_badges.all_badges_dict(bust_cache=True)

            self.redirect("/badges/custom/award")
            return

        self.redirect("/badges/custom/create?failed=1")


class AwardCustomBadge(request_handler.RequestHandler):
    @user_util.developer_required
    def get(self):
        template_values = {
                "custom_badges": custom_badges.CustomBadge.all(),
                }

        self.render_jinja2_template("badges/award_custom_badge.html",
                                    template_values)

    @user_util.developer_required
    def post(self):
        custom_badge_name = self.request_string("name", default="")
        all_custom_badges = custom_badges.CustomBadge.all()
        custom_badge_awarded = None
        emails_awarded = []

        for custom_badge in all_custom_badges:
            if custom_badge.name == custom_badge_name:
                custom_badge_awarded = custom_badge

        if custom_badge_awarded:
            # Award badges and show successful email addresses
            emails_newlines = self.request_string("emails", default="")
            emails = emails_newlines.split()
            emails = map(lambda email: email.strip(), emails)

            for email in emails:
                user_data = \
                    user_models.UserData.get_from_user_input_email(email)
                if user_data:
                    if not custom_badge_awarded.is_already_owned_by(user_data):
                        custom_badge_awarded.award_to(user_data)
                        user_data.put()
                        emails_awarded.append(email)

        template_values = {
                "custom_badges": custom_badges.CustomBadge.all(),
                "custom_badge_awarded": custom_badge_awarded,
                "emails_awarded": emails_awarded
                }

        self.render_jinja2_template("badges/award_custom_badge.html",
                                    template_values)
