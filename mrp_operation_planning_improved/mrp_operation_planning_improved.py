# -*- coding: utf8 -*-
#
#    Copyright (C) 2015 NDP Systèmes (<http://www.ndp-systemes.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from openerp import models, api

class MrpOperationPlanningImproved(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def write(self, vals):
        if vals.get('date_planned'):
            for rec in self:
                if rec.workcenter_lines and vals['date_planned'] > rec.date_planned:
                    rec._compute_planned_workcenter()
        res = super(MrpOperationPlanningImproved, self).write(vals)
        return res
