#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/jinja_filters.py
Benutzerdefinierte Jinja2-Filter
"""

import datetime

def datetime_filter(value, format='%d.%m.%Y %H:%M'):
    """
    Formatiert einen Timestamp oder datetime-Objekt
    
    Args:
        value: Timestamp oder datetime-Objekt
        format: Ausgabeformat für das Datum
    
    Returns:
        Formatierter Datums-String
    """
    if value is None:
        return ''
    
    # Wenn es sich um einen Timestamp handelt
    if isinstance(value, (int, float)):
        value = datetime.datetime.fromtimestamp(value)
    
    # Wenn es sich um ein datetime-Objekt handelt
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    
    return str(value)
