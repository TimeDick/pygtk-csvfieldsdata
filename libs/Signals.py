import gtk
import os, sys

import _csv
from CSV import CSV_Functions as csv
from CSV import UnicodeReader, UnicodeWriter, CSV_Error

class uiSignalHelpers(object):
    def __init__(self, *args, **kwargs):
        super(uiSignalHelpers, self).__init__(*args, **kwargs)
        
    
    def gtk_widget_show(self, w, e = None):
        '''generic function to show gtk widgets/windows
            w - widget to show
        '''
        w.show()
        return True
        
    def gtk_widget_hide(self, w, e = None):
        '''generic function to hide gtk widgets/windows
            w - widget to hide
        '''
        w.hide()
        return True

    def get_web_image(self, url):
        '''retrieve image from web url and return pixbuf
            url - url of image on the web
        '''
        image=gtk.Image()
        response=urllib2.urlopen( url )
        loader=gtk.gdk.PixbufLoader()
        loader.write(response.read())
        loader.close()        
        image.set_from_pixbuf(loader.get_pixbuf())
        return image
        
    def on_column_edited(self, cell, path, new_text, model, treeview = None, data = None ):
        print path, model[path]
        if model[path][0] != new_text: 
            print "Changed '%s' to '%s'" % (model[path][0], new_text)
            model[path][0] = new_text    
        return
        
    def set_selected_field(self, w, e = None):
        if isinstance(w, gtk.TreeSelection):
            w.set_mode(gtk.SELECTION_SINGLE)
            (model, iter) = w.get_selected()
            try:
                val = model.get_value(iter, 0)
                self.selected_field = (val, iter)
            except TypeError, e:
                self.selected_field = (None, None)
        return
    def set_selected_data(self, widget, data = None):
        if isinstance(widget, gtk.TreeSelection):
            widget.set_mode(gtk.SELECTION_SINGLE)
            #( tree_model, tree_iter ) = widget.get_selected()
            self.selected_data = widget.get_selected()
        return
        
    def on_treeview_button_press_event(self, treeview, event):
        print event.button
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)
                
                popupMenu = gtk.Menu()
                menuPopup1 = gtk.ImageMenuItem (gtk.STOCK_OPEN)
                popupMenu.add(menuPopup1)
                menuPopup2 = gtk.ImageMenuItem (gtk.STOCK_OK)
                popupMenu.add(menuPopup2)
                popupMenu.show_all()
                popupMenu.popup( None, None, None, event.button, time)
            return True

    # close the window and quit
    def delete_event(self, widget, event=None, data=None):
        '''quit the application, close window
            if self.parent_app is set beforehand, hide the application window
        '''
        try:
            if not self.parent_app:
                widget.hide()
                return True
            else:
                gtk.main_quit()
                return False
                
        except AttributeError:
            gtk.main_quit()
            return False
                

    def entry_callback(self, w, e=None):
        return self.fields_add_field_data_button_cb(w,e)
                       

WARNING_NEW_MESSAGE = "Unsaved data file detected.\n\nAre you sure you want to create a new data file?"
WARNING_OPEN_MESSAGE = ''
WARNING_SAVE_AS_MESSAGE = ''
WARNING_SAVE_EMPTY_MESSAGE = 'No Data or Fields to save.\n\nAre you sure you want to save a emppty file?'
class uiSignals(uiSignalHelpers):
    def __init__(self, *args, **kwargs):
        super(uiSignals, self).__init__(*args, **kwargs)
    
    def fields_clear_field_data_button_cb(self, w, e = None):
        for field in range(len(self.fields)):
            self.form_fields["form_fields_%s_entry" % ( self.fields[field] )].set_text('')
        return
        
    def fields_remove_field_data_button_cb(self, w, e = None):
        try:
            ( model, iter ) = self.selected_data
    
            if iter and model:
                id = model.get_value( iter, 0 )
                del self.fields_data[ int( id ) - 1 ]
                for data in range( len( self.fields_data ) ):
                    self.fields_data[ data ][ '_id_' ] = data + 1
            self.update_all()
        except AttributeError, e:
            #nothing was selected in the treeview
            pass
        
        return
        
        
    def fields_remove_field_button_cb(self, w, e=None):
        try:
            sele, seli = self.selected_field
            if sele:
                if self.fields.index(sele) != -1:
                    del self.fields[ self.fields.index(sele) ]
                    for data in self.fields_data:
                        for item in data.keys():
                            if sele == item:
                                del data[item]
            self.update_all()
        except AttributeError, e:
            #nothing was selected in the treeview
            pass
        return 
        
    def fields_add_field_data_button_cb( self, w, e = None ):
        
        idx = self.selected_data_idx
        self.selected_data_idx = None
        if idx:
            del self.fields_data[idx - 1]
            fields_data_text = { '_id_' : self.fields_order_data_spinbutton.get_value_as_int() }
        else:
            fields_data_text = { '_id_' : len( self.fields_data ) + 1 }
            
        #insert fields_data
        for field in range(len(self.fields)):
            data = self.form_fields["form_fields_%s_entry" % ( self.fields[field] )].get_text()
            fields_data_text[ self.fields[ field ] ] = data
        self.fields_data.insert( self.fields_order_data_spinbutton.get_value_as_int() - 1, fields_data_text )
        
        #fix ids
        for data in range( len( self.fields_data ) ):
            self.fields_data[ data ][ '_id_' ] = data + 1
        
        self.focus(self.fields_clear_field_data_button)
        self.update_all()
        return

        
    def fields_add_field_button_cb(self, w, e=None):
        field_name = self.fields_new_field_entry.get_text()
        if field_name:            
            field_name = self.clean_data(field_name)

            if field_name != '_id_':
                if field_name in self.fields:
                    self.clear_focus(self.fields_new_field_entry)
                    return

                self.fields.insert( self.fields_order_spinbutton.get_value_as_int() - 1 , field_name )

        self.clear_focus(self.fields_new_field_entry)
        self.update_all()
        return
    
    def fields_edit_field_data_button_cb(self, w, e = None):
        if self.selected_data:
            (tree_model, tree_iter) = self.selected_data
            #selected_item = ()
            try:
                self.selected_data_idx = int( tree_model.get_value( tree_iter, 0 ) )
            except TypeError, e:
                pass
            try:
                for item in range( len( self.fields ) ):
                    value = tree_model.get_value(tree_iter, item + 1 )
                    #selected_item += ( value, )
                    self.form_fields["form_fields_%s_entry" % ( self.fields[ item ] ) ].set_text( value ) 
            except TypeError, e:
                pass
            #self.update_all()
        return
        
        
    def fields_new_menuitem_cb(self, w, e=None):
        if self.fields:
            if self.show_warning( WARNING_NEW_MESSAGE ):
                self.init()
                self.update_all()
        return
        
    def fields_open_menuitem_cb(self, w, e=None):
        if self.fields:
            if self.show_warning( WARNING_OPEN_MESSAGE ):
                self.run_open_dialog()
        else:    
            self.run_open_dialog()
        self.update_all()           
        return
        
    def fields_save_as_menuitem_cb(self, w, e=None):
        if self.fields:
            #if self.show_warning( WARNING_SAVE_AS_MESSAGE ):
            self.csv_filename = self.run_save_dialog(self.save_csv_file, self.fields, self.fields_data)
        else:
            if self.show_warning( WARNING_SAVE_EMPTY_MESSAGE ):
               self.csv_filename = self.run_save_dialog(self.save_csv_file, self.fields, self,fields_data)
        #self.update_all()
        return
        
    def fields_save_menuitem_cb(self, w, e=None):
        if self.csv_filename:
            self.save_csv_file(self.csv_filename, self.fields, self.fields_data)
        else:
            self.csv_filename = self.run_save_dialog(self.save_csv_file, self.fields, self.fields_data)
        #self.update_all()
        return    
    
