from flask_wtf import FlaskForm
import secret
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms import Form, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask import Flask, render_template, url_for, flash, redirect

# create some fields


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField(
        'Password', validators=[
            DataRequired(), Length(
                min=6, max=50)])
    confirm_password = PasswordField(
        'Confirm Password', validators=[
            DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Sign in')


class ProductSearchForm(FlaskForm):
    #     choices = [('Artist', 'Artist'),
    #                ('Album', 'Album'),
    #                ('Publisher', 'Publisher')]

    #     select = SelectField('Search for music:', choices=choices)
    search = StringField('')
    submit = SubmitField('Search')
