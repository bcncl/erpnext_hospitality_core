frappe.ui.form.on('Hotel Group Booking', {
    refresh: function (frm) {
        if (!frm.is_new()) {

            // Button: Create Master Folio
            if (!frm.doc.master_folio) {
                frm.add_custom_button(__('Create Master Folio'), function () {
                    frm.call({
                        method: 'hospitality_core.hospitality_core.api.group_booking.create_master_folio',
                        args: { group_booking_name: frm.doc.name },
                        freeze: true,
                        callback: function (r) {
                            if (!r.exc) frm.reload_doc();
                        }
                    });
                }).addClass("btn-primary");
            } else {
                // Link to Folio
                frm.add_custom_button(__('View Master Folio'), function () {
                    frappe.set_route('Form', 'Guest Folio', frm.doc.master_folio);
                });
            }

            // Button: Add Reservations
            frm.add_custom_button(__('Link Reservations'), function () {
                new frappe.ui.form.MultiSelectDialog({
                    doctype: "Hotel Reservation",
                    target: frm,
                    setters: {
                        status: 'Reserved',
                    },
                    get_query() {
                        return {
                            filters: {
                                'group_booking': ['is', 'not set'],
                                'status': 'Reserved'
                            }
                        };
                    },
                    action(selections) {
                        if (selections.length === 0) {
                            frappe.msgprint(__('Please select at least one reservation.'));
                            return;
                        }
                        frm.call({
                            method: 'hospitality_core.hospitality_core.api.group_booking.add_rooms_to_group',
                            args: {
                                group_booking: frm.doc.name,
                                rooms: JSON.stringify(selections)
                            },
                            freeze: true,
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint(__('Reservations linked successfully.'));
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });
            });

            // Button: Bulk Reserve
            frm.add_custom_button(__('Bulk Reserve'), function () {
                if (!frm.doc.arrival_date || !frm.doc.departure_date) {
                    frappe.msgprint(__('Please set Arrival and Departure dates for the group first.'));
                    return;
                }

                let d = new frappe.ui.Dialog({
                    title: __('Bulk Reservation'),
                    fields: [
                        {
                            label: __('Guest'),
                            fieldname: 'guest',
                            fieldtype: 'Link',
                            options: 'Guest',
                            reqd: 1
                        },
                        {
                            label: __('Room Type'),
                            fieldname: 'room_type',
                            fieldtype: 'Link',
                            options: 'Hotel Room Type'
                        },
                        {
                            label: __('Discount Type'),
                            fieldname: 'discount_type',
                            fieldtype: 'Select',
                            options: '\nPercentage\nAmount'
                        },
                        {
                            label: __('Discount Value'),
                            fieldname: 'discount_value',
                            fieldtype: 'Currency'
                        },
                        {
                            label: __('Available Rooms'),
                            fieldname: 'rooms_html',
                            fieldtype: 'HTML'
                        }
                    ],
                    primary_action_label: __('Reserve'),
                    primary_action(values) {
                        let selected_rooms = [];
                        d.$wrapper.find('.room-checkbox:checked').each(function () {
                            selected_rooms.push($(this).val());
                        });

                        if (selected_rooms.length === 0) {
                            frappe.msgprint(__('Please select at least one room.'));
                            return;
                        }

                        frappe.call({
                            method: 'hospitality_core.hospitality_core.api.group_booking.bulk_reserve_rooms',
                            args: {
                                group_booking: frm.doc.name,
                                guest: values.guest,
                                rooms: JSON.stringify(selected_rooms),
                                arrival_date: frm.doc.arrival_date,
                                departure_date: frm.doc.departure_date,
                                discount_type: values.discount_type || null,
                                discount_value: values.discount_value || 0
                            },
                            freeze: true,
                            callback: function (r) {
                                if (!r.exc) {
                                    let msg = __('Successfully reserved {0} rooms.').format(r.message.created.length);
                                    let indicator = 'green';

                                    if (r.message.errors && r.message.errors.length > 0) {
                                        msg += "<br><br>" + __("<b>Failures:</b>") + "<br><ul><li>" + r.message.errors.join("</li><li>") + "</li></ul>";
                                        indicator = 'orange';
                                    }

                                    frappe.msgprint({
                                        title: __('Bulk Reservation Status'),
                                        message: msg,
                                        indicator: indicator
                                    });

                                    if (r.message.created.length > 0) {
                                        d.hide();
                                        frm.reload_doc();
                                    }
                                }
                            }
                        });
                    }
                });

                d.fields_dict.room_type.df.onchange = () => {
                    refresh_rooms();
                };

                let refresh_rooms = () => {
                    let room_type = d.get_value('room_type') || '';
                    frappe.call({
                        method: 'hospitality_core.hospitality_core.api.reservation.get_available_rooms_for_picker',
                        args: {
                            doctype: 'Hotel Room',
                            txt: '',
                            searchfield: 'name',
                            start: 0,
                            page_len: 200,
                            filters: {
                                arrival_date: frm.doc.arrival_date,
                                departure_date: frm.doc.departure_date,
                                room_type: room_type
                            }
                        },
                        callback: function (r) {
                            let rooms = r.message || [];
                            let html = '<div style="max-height: 250px; overflow-y: auto; border: 1px solid #d1d8dd; border-radius: 4px; padding: 10px; background: #f8f9fa;">';
                            if (rooms.length === 0) {
                                html += `<p class="text-muted text-center">${__('No rooms available for the selected dates/type.')}</p>`;
                            } else {
                                html += '<div class="row">';
                                rooms.forEach(room => {
                                    html += `
                                        <div class="col-sm-6">
                                            <div class="checkbox" style="margin-top: 5px; margin-bottom: 5px;">
                                                <label style="font-weight: normal; cursor: pointer;">
                                                    <input type="checkbox" class="room-checkbox" value="${room[0]}">
                                                    <span class="label label-info" style="margin-right: 5px;">${room[0]}</span>
                                                    <small class="text-muted">${room[1]}</small>
                                                </label>
                                            </div>
                                        </div>
                                    `;
                                });
                                html += '</div>';
                            }
                            html += '</div>';
                            d.fields_dict.rooms_html.$wrapper.html(html);
                        }
                    });
                };

                d.show();
                refresh_rooms();
            }, __('Actions'));

            // Button: Mass Check In
            if (frm.doc.status === 'Confirmed' || frm.doc.status === 'In House') {
                frm.add_custom_button(__('Check In Group'), function () {
                    frappe.confirm('Check In all RESERVED guests in this group?', () => {
                        frm.call({
                            method: 'hospitality_core.hospitality_core.api.group_booking.mass_check_in',
                            args: { group_booking: frm.doc.name },
                            freeze: true,
                            callback: function (r) {
                                if (!r.exc) {
                                    let indicator = (r.message.error_count > 0) ? 'orange' : 'green';
                                    frappe.msgprint({
                                        title: __('Group Check-In Status'),
                                        message: r.message.message,
                                        indicator: indicator
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    });
                }, 'Actions');
            }

            // Button: Mass Check Out
            if (frm.doc.status === 'In House' || frm.doc.status === 'Checked Out') {
                frm.add_custom_button(__('Check Out Group'), function () {
                    frappe.confirm('Check Out all IN-HOUSE guests in this group?', () => {
                        frm.call({
                            method: 'hospitality_core.hospitality_core.api.group_booking.mass_check_out',
                            args: { group_booking: frm.doc.name },
                            freeze: true,
                            callback: function (r) {
                                if (!r.exc) {
                                    let indicator = (r.message.error_count > 0) ? 'orange' : 'green';
                                    frappe.msgprint({
                                        title: __('Group Check-Out Status'),
                                        message: r.message.message,
                                        indicator: indicator
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    });
                }, 'Actions');
            }
        }
    }
});