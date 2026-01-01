# Sistema de Gestión de Roles y Horarios

Este proyecto es una aplicación web desarrollada en Django para la gestión de turnos y disponibilidad de voluntarios en una iglesia o organización similar.

## Características Principales

*   **Gestión de Usuarios y Roles:** Asignación de roles (Sonido, Multimedia, Aseo, etc.) a usuarios.
*   **Definición de Disponibilidad:** Los usuarios pueden marcar sus excepciones (cuándo NO pueden servir).
*   **Algoritmo de Programación:** Generación automática de horarios basada en reglas de negocio y disponibilidad.
*   **Notificaciones:** Envío de recordatorios por correo electrónico y enlaces para WhatsApp.

## Tecnologías

*   Python 3.x
*   Django 5.2.9
*   Bootstrap 5
*   SQLite

## Configuración

1.  Clonar el repositorio.
2.  Crear un entorno virtual: `python -m venv .venv`
3.  Activar el entorno virtual.
4.  Instalar dependencias: `pip install -r requirements.txt`
5.  Ejecutar migraciones: `python manage.py migrate`
6.  Crear superusuario: `python manage.py createsuperuser`
7.  Iniciar el servidor: `python manage.py runserver`
