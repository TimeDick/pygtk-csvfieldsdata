import os, sys
import gtk, gobject
import string

class InterfaceException(Exception):
    pass

class ParameterException(Exception):
    pass

class FunctionParameterException(ParameterException):
    pass
    
try:
    from UI import uiBuilder, uiCreator, uiTreeView, uiLabel, uiEntry
except ImportError:
    raise 'User Interface Import Error'
    sys.exit(1)
    

from CSV import CSV_Functions as csv
from O import objectify, object_caller

class CSV_Header_Exception(Exception):
    pass
            
class logicHelpers(objectify):
    def __init__(self, *args, **kwargs):
        super(logicHelpers, self).__init__(*args, **kwargs)

    def clear_treeview(self, treeview):
        treeview.get_model().clear()
        
    def clear_entry(self, entry):
        entry.set_text('')
    
    def focus(self, control):
        control.grab_focus()

    def clear_focus(self, control):
        self.clear_entry(control)
        self.focus(control)
        return
        
    def sensitive(self, control, bool = False):
        control.set_sensitive( bool )

    def show_warning(self, message):
        self.warning_dialog_message_label.set_text( message )
        return self.warning_dialog.run()
    
    def _add_row_to_treeview(self, treeview, items = [], iter = None):
        print items
        iter = treeview.add_row( items, iter)
        return iter
            #for name, value in self.config.items( section ):
            #     self.config_treeview.add_row([ section, name, value, False ], section_iter)        
    
    def run_open_dialog(self):
        if self.open_dialog.run():
            self.init()
            #self.update_all()
            #self.fields_statusbar_label.set_text('Go!') 
            csv_filename = self.open_dialog.get_filename()
            reader = csv.get_reader( csv_filename )
            
            #this will fail if null bytes are found, as in xls files
            self.fields = reader.next()      
            
            error_found = False
            for i in range( len( self.fields ) ):
                if not self.fields[i]:
                    error_found = True
                    #raise CSV_Header_Exception, 'Empty Header Fields Found in CSV File :('
            if error_found:
                self.show_warning('Error: Empty Header Fields found in CSV File :(')
            
            is_data = True
            idx = 1
            while is_data:
                try:
                    self.fields_data.append( dict( zip( [ '_id_' ] + self.fields, [ idx ] + reader.next() ) ) )
                    idx += 1
                except (StopIteration):
                    is_data = False

    def save_csv_file(self, filename, cols, data):
        if filename:
            writer = csv.get_writer( filename )

            #columns
            writer.writerow( cols )
                
            #rows
            for row in data:
                reordered = []
                for field in cols:
                    reordered.append( "%s" % ( row[field] ) )
                writer.writerow( reordered )
                
    def run_save_dialog(self, callback = None, *args, **kwargs):
        if callback and self.save_dialog.run():
            filename = self.save_dialog.get_filename()
            #self.save_csv_file(filename, self.fields, self.fields_data)
            callback(filename, *args)
            return filename

class logicFunctions(logicHelpers):
    def __init__(self, *args, **kwargs):
        super(self, logicFunctions).__init__(*args, **kwargs) 
        
    def init(self, *args, **kwargs):
        self.fields = []
        self.form_fields = {}
        self.csv_filename = kwargs.get('filename', '')
        self.fields_data = []
        #self.fields_data_text = []
        self.temp_containers = {}
        self.focus_location = ''
        self.selected_data_idx = None
        
    def button_sensitivity(self):
        if not self.fields_data:
            self.sensitive(self.fields_clear_field_data_button, False)
            self.sensitive(self.fields_add_field_data_button, False)
            self.sensitive(self.fields_remove_field_data_button, False)
            self.sensitive(self.fields_edit_field_data_button, False)
            if not self.fields:
                self.sensitive(self.fields_remove_field_button, False)
            else:
                self.sensitive(self.fields_remove_field_button, True)
                self.sensitive(self.fields_clear_field_data_button, True)
                self.sensitive(self.fields_add_field_data_button, True)
        else:
            self.sensitive(self.fields_clear_field_data_button, True)
            self.sensitive(self.fields_add_field_data_button, True)
            self.sensitive(self.fields_remove_field_data_button, True)
            self.sensitive(self.fields_edit_field_data_button, True)
            
    def _create_form_fields(self, form_box ):
        try:
            form_box.remove(self.temp_form_box)
            del self.temp_form_scroll
        except AttributeError:
            pass
        self.temp_form_box = gtk.VBox(True, 0)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        box = gtk.VBox(False, 0)
        for field in range(len(self.fields)):
            f = self.fields[field]
            self.form_fields["form_fields_%s_label" % ( f )] = gtk.Label("%s : %s " % (field + 1, f) )
            self.form_fields["form_fields_%s_label" % ( f )].set_alignment(5, 0.5)
            
            self.form_fields["form_fields_%s_entry" % ( f )] = gtk.Entry()
            self.form_fields["form_fields_%s_entry" % ( f )].connect("activate", self.entry_callback, self.form_fields["form_fields_%s_entry" % ( f )] )

            
            self.form_fields['form_fields_%s_hbox' % ( f )] = gtk.HBox(False, 0)
            

            self.form_fields['form_fields_%s_hbox' % ( f )].pack_start(self.form_fields["form_fields_%s_label" % ( f )])
            self.form_fields['form_fields_%s_hbox' % ( f )].pack_start(self.form_fields["form_fields_%s_entry" % ( f )])
            
            box.pack_start(self.form_fields['form_fields_%s_hbox' % ( f )])
            
            
        scroll.add_with_viewport(box)
        self.temp_form_box.pack_start(scroll)
        form_box.pack_start(self.temp_form_box,True,True,0) 
        form_box.show_all()
    

    def _update_treeview(self, treeview, items={}, order_list = []):
        print 'items:', items
        print 'order:', order_list
        field_iter = None
        if isinstance(items, dict): 
            for field in items.keys():
                self._add_row_to_treeview(treeview, [field, items[field]], None)
        if isinstance(items, list):
            for i in range(1, len(items) + 1):
                if isinstance(items[i - 1], list):
                    self._add_row_to_treeview(treeview, items[i - 1])
                elif isinstance(items[i - 1], dict):
                    if order_list:
                        item = []
                        for j in order_list:
                            item.append(items[i - 1][j])

                        self._add_row_to_treeview(treeview, item)
                else:
                    self._add_row_to_treeview(treeview, [items[i - 1], i])
                    
    def _reset_spin_range( self, spin, list, idx = None ):
        spin.set_range( 1, len( list ) + 1 )  
        if not idx:
            spin.set_value( len( list ) + 1 )
        else:
            spin.set_value( idx )
            
    def fix_col_len(self, data):
        for f in range(len(data)):
            while(len(data[f].keys()) < len(data[-1].keys())):
                for fd in data[-1].keys():
                    if fd not in data[f].keys():
                        data[f].update({ fd : '', '_id_' : f })
                        
    def clean_data(self, data = None, concat = '_'):
        if data:
            for i in data:
                if not i in string.ascii_letters + string.digits:
                    data = concat.join(data.split( i ))
        return data
    def update_all(self): 

        self.button_sensitivity()
        
        self.fix_col_len(self.fields_data)
        
        self.clear_treeview(self.fields_treeview)
        self.clear_treeview(self.fields_data_treeview)
        
        self._reset_spin_range(self.fields_order_spinbutton, self.fields)
        
        self._update_treeview(self.fields_treeview, self.fields)        
        
        if not self.selected_data_idx:  
            self.fields_data_id_label.set_text('%s' % ( len(self.fields_data) + 1 ) )
            self._reset_spin_range(self.fields_order_data_spinbutton, self.fields_data)
            self._create_form_fields(self.fields_form_box)
            #self.create_treeview( container = self.fields_data_box, container_name = 'fields_data', cols = self.fields )
        
            self.fields_data_obj( self.create_treeview, cols = [ '_id_' ] + self.fields )
        
            self._update_treeview(self.fields_data_treeview, self.fields_data, [ '_id_' ] + self.fields)
        else:
            self.fields_data_id_label.set_text('%s' % ( self.selected_data_idx ) )
            self._reset_spin_range(self.fields_order_data_spinbutton, self.fields_data, self.selected_data_idx)
            
class uiLogic(uiBuilder, uiCreator, logicFunctions):
    def __init__(self,*args, **kwargs):
        super(uiLogic, self).__init__(*args, **kwargs)
        
        #get all the widgets from the glade ui file
        if self.builder_build(widget_list_dict = {}, *args, **kwargs):
            #self.fields_window.set_decorated(False)
            #self.fields_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)

            #initialize application
            self.init()
            
            #init fields treeview object_caller
            self.fields_obj = object_caller(
                container = self.fields_box,
                container_name = 'fields',
                cols = [ 'Name', 'Order' ],
                cursor_changed = self.set_selected_field,
                button_press = self.on_treeview_button_press_event,
                column_edited = self.on_column_edited
            )
            #fields treeview object call
            self.fields_obj( self.create_treeview )
            
            #init fields_data treeview object_caller 
            self.fields_data_obj = object_caller(
                container = self.fields_data_box,
                container_name = 'fields_data',
                cols = self.fields, #[ '_id_' ] + self.fields,
                cursor_changed = self.set_selected_data,
                button_press = self.on_treeview_button_press_event,
                column_edited = self.on_column_edited
            )
            #fields_data treeview object call
            self.fields_data_obj( self.create_treeview )
            
            self.button_sensitivity()
            
            #show the main window of the application
            self.fields_window.show_all()
            #self.update_all()
