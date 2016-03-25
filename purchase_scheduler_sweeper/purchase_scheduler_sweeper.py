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

from openerp import models, api, fields, _
import logging
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSessionHandler, ConnectorSession

PURCHASE_CHUNK = 100

_logger = logging.getLogger(__name__)


@job(default_channel='root.posweeper')
def job_purchase_order_sweeper(session, model_name, ids):
    model_instance = session.pool[model_name]
    model_instance.sweep(session.cr, session.uid, ids, context=session.context)
    return _('Chunk of %s purchase orders sweeped') % len(ids)


class PurchaseOrderSweeper(models.TransientModel):
    _name = 'purchase.order.sweeper'

    @api.multi
    def launch_job_purchase_order_sweeper(self):
        self.env['purchase.order'].chunk_sweep()


class SweeperPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    minimum_planned_date = fields.Date(string='Expected Date', index=True,
                                       help="This is computed as the minimum scheduled date of all purchase order "
                                            "lines' products.")

    @api.model
    def chunk_sweep(self):
        orders = self.env['purchase.order'].search([('state', '=', 'draft')])
        session = ConnectorSession.from_env(self.env)
        while orders:
            chunk_orders = orders[:PURCHASE_CHUNK]
            orders = orders[PURCHASE_CHUNK:]
            description = _('Chunk of %s purchase orders to sweep') % len(chunk_orders)
            job_purchase_order_sweeper.delay(session, 'purchase.order', chunk_orders.ids, description=description,
                                             priority=1)

    @api.multi
    def sweep(self):
        _logger.info(_("<<< Started chunk of %s purchase orders to sweep") % len(self))
        for order in self:
            for line in order.order_line:
                # Clean lines and rerun procurements
                if line.procurement_ids and line.state == 'draft':
                    procs = line.procurement_ids
                    line.unlink()
                    procs.run()
            if order.order_line:
                # Update minimum planned date that is no longer a function
                min_date = order.order_line[0].date_planned
                for line in order.order_line:
                    if line.state == 'cancel':
                        continue
                    if line.date_planned < min_date:
                        min_date = line.date_planned
                order.minimum_planned_date = min_date
        # Now delete empty purchase orders
        self.env['purchase.order'].search([('state', '=', 'draft'), ('order_line', '=', False)]).unlink()
        _logger.info(_(">>> End of chunk"))
