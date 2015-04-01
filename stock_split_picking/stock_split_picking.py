# -*- coding: utf8 -*-
#
# Copyright (C) 2014 NDP Systèmes (<http://www.ndp-systemes.fr>).
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
from datetime import datetime

from openerp import fields, models, api

class stock_split_only_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_split_only(self):
        self.with_context(do_only_split=True).do_detailed_transfer()

    @api.multi
    def save_transfer(self):
        """ Save the current wizard into the picking's pack operations and reloads the wizard.
        :return: An action to this wizard
        """
        self.ensure_one()
        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                if prod.packop_id:
                    prod.packop_id.write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', self.picking_id.id),
                                                                '!', ('id', 'in', processed_ids)])
        for packop in packops:
            packop.unlink()
        return self.wizard_view()


class stock_split_picking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def action_split_from_ui(self):
        """ called when button 'done' is pushed in the barcode scanner UI """
        #write qty_done into field product_qty for every package_operation before doing the transfer
        for operation in self.pack_operation_ids:
            operation.write({'product_qty': operation.qty_done})
        self.do_split()
