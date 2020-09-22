# -*- coding: utf-8 -*-
# Copyright (c) 2020, ifitwala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, today 
from frappe.model.document import Document
from frappe.desk.form.linked_with import get_linked_doctypes

class Student(Document):
	
	def validate(self): 
            self.title = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
            
            if frappe.get_value("Student", self.name, "title") != self.title: 
                    self.update_student_name_in_linked_doctype()
            
            if self.date_of_birth and getdate(self.date_of_birth) >= getdate(today()): 
                    frappe.throw(_("Check again student's birth date.  It cannot be after today."))
            
            if self.date_of_birth and getdate(self.date_of_birth) >= getdate(self.joining_date): 
                    frappe.throw(_("Check again student's birth date and or joining date. Birth date cannot be after joining date.")) 
                    
            if self.joining_date and self.exit_date and getdate(self.joining_date) > getdate(self.exit_date): 
                    frappe.throw(_("Check again the exit date. The joining date has to be earlier than the exit date."))

            
    
	def update_student_name_in_linked_doctype(self):
		linked_doctypes = get_linked_doctypes("Student")
		for d in linked_doctypes:
			meta = frappe.get_meta(d)
			if not meta.issingle:
				if "student_name" in [f.fieldname for f in meta.fields]:
					frappe.db.sql("""UPDATE `tab{0}` set student_name = %s where {1} = %s"""
						 .format(d, linked_doctypes[d]["fieldname"][0]),(self.title, self.name))

				if "child_doctype" in linked_doctypes[d].keys() and "student_name" in \
					[f.fieldname for f in frappe.get_meta(linked_doctypes[d]["child_doctype"]).fields]:
					frappe.db.sql("""UPDATE `tab{0}` set student_name = %s where {1} = %s"""
						  .format(linked_doctypes[d]["child_doctype"], linked_doctypes[d]["fieldname"][0]),(self.title, self.name))
	
	def after_insert(self): 
		self.create_student_user()
		self.create_student_patient()
	
	# create student as website user
	def create_student_user(self): 
		if not frappe.db.exists("User", self.student_email): 
			student_user = frappe.get_doc({
				"doctype": "User", 
				"first_name": self.first_name, 
				"last_name": self.last_name, 
				"email": self.student_email, 
				"username": self.student_email, 
				"gender": self.gender, 
				"language": self.first_language, 
				"send_welcome_email": 1, 
				"user_type": "Website User"
				})
			student_user.flags.ignore_permissions = True
			student_user.add_roles("Student")
			student_user.save()
			update_password_link = student_user.reset_password()
			frappe.msgprint(_("User {0} has been created").format(self.student_email))
			
	# Create student as patient 
	def create_student_patient(self): 
		if not frappe.db.exists("Student Patient", {"student_name": self.title}): 
			student_patient = frappe.get_doc({
				"doctype": "Student Patient", 
				"student": self.name
				})
			student_patient.save()
			frappe.msgprint(_("Student Patient {0} linked to this student has been created").format(self.title))

			
	def enroll_in_course(self, course_name, program_enrollment, enrollment_date):
		try:
			enrollment = frappe.get_doc({
					"doctype": "Course Enrollment",
					"student": self.name,
					"course": course_name,
					"program_enrollment": program_enrollment,
					"enrollment_date": enrollment_date
				})
			enrollment.save(ignore_permissions=True)
		except frappe.exceptions.ValidationError:
			enrollment_name = frappe.get_list("Course Enrollment", filters={"student": self.name, "course": course_name, "program_enrollment": program_enrollment})[0].name
			return frappe.get_doc("Program Enrollment", enrollment_name)
		else:
			return enrollment


            
