"""
my_projekt.py

Dieses Modul stellt eine GUI-Anwendung zur Echtzeit-Visualisierung und Speicherung von seriellen Daten bereit.

Klassen:
    SerielleApp: Haupt-GUI-Klasse zur Verwaltung der seriellen Kommunikation.
    MockSerial: Klasse zur Simulation einer seriellen Schnittstelle für Testzwecke.
    SerielleKom: Klasse zur Verwaltung der seriellen Kommunikation.

Hauptprogramm:
    Startet die GUI-Anwendung und eine Testinstanz der seriellen Kommunikation.
"""

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
import threading
import serial
from datetime import datetime
import csv

class SerielleApp:
    """
    Diese Klasse stellt die Haupt-GUI-Anwendung für die serielle Kommunikation dar.

    :param master: Das Hauptfenster der Tkinter-Anwendung.
    :type master: tk.Tk
    """
    def __init__(self, master):
        """
        Initialisiert die GUI-Komponenten und setzt den Titel des Hauptfensters.
        
        :param master: Das Hauptfenster der Tkinter-Anwendung.
        :type master: tk.Tk
        """
        self.master = master
        self.master.title("Serielle Kommunikation")
        
        # COM-Manager Frame erstellen
        self.rahmen_com = ttk.LabelFrame(master, text="COM-Manager")
        self.rahmen_com.grid(column=0, row=0, padx=10, pady=10)
        
        # Variablen für COM-Port und Baudrate
        self.com_var = tk.StringVar(value="COM1")
        self.baud_var = tk.StringVar(value='9600')
        
        # Label und Eingabefeld für COM-Port
        self.com_label = ttk.Label(self.rahmen_com, text="Verfügbare Port(s):")
        self.com_label.grid(column=0, row=0, padx=5, pady=5)
        
        self.com_eingabe = ttk.Combobox(self.rahmen_com, textvariable=self.com_var)
        self.com_eingabe.grid(column=1, row=0, padx=5, pady=5)
        
        # Label und Eingabefeld für Baudrate
        self.baud_label = ttk.Label(self.rahmen_com, text="Baudrate:")
        self.baud_label.grid(column=0, row=1, padx=5, pady=5)
        
        self.baud_eingabe = ttk.Entry(self.rahmen_com, textvariable=self.baud_var)
        self.baud_eingabe.grid(column=1, row=1, padx=5, pady=5)
        
        # Buttons zum Aktualisieren und Verbinden
        self.aktualisieren_button = ttk.Button(self.rahmen_com, text="Aktualisieren", command=self.aktualisiere_ports)
        self.aktualisieren_button.grid(column=0, row=2, padx=5, pady=5)
        
        self.verbinden_button = ttk.Button(self.rahmen_com, text="Verbinden", command=self.verbinden)
        self.verbinden_button.grid(column=1, row=2, padx=5, pady=5)
        
        # Verbindungs-Manager Frame erstellen
        self.rahmen_verbindung = ttk.LabelFrame(master, text="Verbindungs-Manager")
        self.rahmen_verbindung.grid(column=0, row=1, padx=10, pady=10)
        
        # Buttons zum Starten und Stoppen der Datenaufnahme
        self.start_button = ttk.Button(self.rahmen_verbindung, text="Start", command=self.start)
        self.start_button.grid(column=0, row=0, padx=5, pady=5)
        
        self.speichern_button = ttk.Button(self.rahmen_verbindung, text="Speichern", command=self.speichern)
        self.speichern_button.grid(column=2, row=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self.rahmen_verbindung, text="Stop", command=self.stop)
        self.stop_button.grid(column=1, row=0, padx=5, pady=5)
        
        # Diagramm zur Datenanzeige erstellen
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Sinus")
        
        self.leinwand = FigureCanvasTkAgg(self.fig, master=self.master)
        self.leinwand.get_tk_widget().grid(column=1, row=0, rowspan=2, padx=1, pady=10)
        
        # Steuerungsvariablen
        self.laeuft = False
        self.start_zeit = time.time()
        self.daten = []
        self.serielle_kom = SerielleKom(port='COM3', baudrate=9600, use_mock=True)

    def aktualisiere_ports(self):
        """
        Aktualisiert die Liste der verfügbaren COM-Ports.
        Hier wird dies nur simuliert.
        """
        verfuegbare_ports = ['COM1', 'COM2', 'COM3']
        self.com_eingabe['values'] = verfuegbare_ports

    def verbinden(self):
        """
        Verbindet sich mit dem ausgewählten seriellen Port.
        """
        if self.serielle_kom.verbinden():
            self.verbinden_button.config(state='disabled')
            self.aktualisieren_button.config(state='disabled')
            self.com_eingabe.config(state='disabled')
            self.baud_eingabe.config(state='disabled')
        else:
            tk.messagebox.showerror("Verbindungsfehler", "Konnte keine Verbindung herstellen.")

    def start(self):
        """
        Startet die Datenaufnahme.
        """
        if self.serielle_kom.verbinden():
            self.laeuft = True
            self.start_zeit = time.time()  # Startzeit zurücksetzen
            self.daten = []
            self.aktualisiere_diagramm()

    def aktualisiere_diagramm(self):
        """
        Aktualisiert das Diagramm mit neuen Daten, solange die Aufnahme läuft.
        """
        ZEITFENSTER = 10  # Zeitfenster in Sekunden

        if self.laeuft:
            daten = self.serielle_kom.lese_daten()
            aktuelle_zeit = time.time()
            if daten is not None:
                # Erstelle ein Tuple von (Zeit, Wert) für jeden neuen Datenpunkt
                neue_daten = [(aktuelle_zeit + i * (1/len(daten)), wert) for i, wert in enumerate(daten)]
                self.daten.extend(neue_daten)

                # Entferne Daten, die älter sind als das Zeitfenster
                self.daten = [(zeit, wert) for zeit, wert in self.daten if zeit >= aktuelle_zeit - ZEITFENSTER]

                # Extrahiere die Zeiten und Werte für das Plotten
                zeiten, werte = zip(*self.daten)
                zeiten = [t - min(zeiten) for t in zeiten]  # Normalisiere die Zeitwerte zum Startpunkt des Fensters

                self.ax.cla()  # Löscht die aktuelle Achse
                self.ax.plot(zeiten, werte, label='Datenverlauf')  # Fügt Daten mit Label hinzu
                self.ax.set_title('Echtzeit-Datenvisualisierung')  # Setzt den Titel des Diagramms
                self.ax.set_xlabel('Zeit (s)')  # Setzt die Beschriftung der x-Achse
                self.ax.set_ylabel('Wert')  # Setzt die Beschriftung der y-Achse
                self.ax.legend()  # Fügt eine Legende hinzu
                self.leinwand.draw()
            
            # Aktualisiert das Diagramm alle 100 ms
            self.master.after(100, self.aktualisiere_diagramm)
        else:
        # Wenn laeuft False ist, zeige alle gesammelten Daten an
            if self.daten:
                zeiten, werte = zip(*self.daten)
                startzeit = min(zeiten)
                zeiten = [t - startzeit for t in zeiten]  # Normalisiere die Zeitwerte zum Startpunkt des Fensters
                
                self.ax.cla()  # Löscht die aktuelle Achse
                self.ax.plot(zeiten, werte, label='Gesamte Daten')  # Fügt Daten mit Label hinzu
                self.ax.set_title('Gesamte Datenvisualisierung')  # Setzt den Titel des Diagramms
                self.ax.set_xlabel('Zeit (s)')  # Setzt die Beschriftung der x-Achse
                self.ax.set_ylabel('Wert')  # Setzt die Beschriftung der y-Achse
                self.ax.legend()  # Fügt eine Legende hinzu
                self.leinwand.draw()

    def stop(self):
        """
        Stoppt die Datenaufnahme.
        """
        self.laeuft = False
        self.aktualisiere_diagramm()

    def speichern(self):
        """
        Speichert die Daten in einer CSV-Datei.
        """
        if self.daten:
            dateiname = datetime.now().strftime("daten_%Y%m%d_%H%M%S.csv")
            with open(dateiname, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Index', 'Wert'])
                for index, wert in enumerate(self.daten):
                    writer.writerow([index, wert])
            tk.messagebox.showinfo("Speichern erfolgreich", f"Daten wurden in {dateiname} gespeichert.")
        else:
            tk.messagebox.showwarning("Keine Daten", "Es gibt keine Daten zu speichern.")

class MockSerial:
    """
    Eine simulierte serielle Schnittstelle zum Testen.
    """
    def __init__(self, *args, **kwargs):
        self.is_open = False
        self.status = False
        self.buffer = []
        self.timeout = None
        self.running = False

    def open(self):
        """
        Öffnet den Mock-Port.
        """
        self.is_open = True
        self.status = True
        self.running = True
        self.start_generating_data()

    def close(self):
        """
        Schließt den Mock-Port.
        """
        self.is_open = False
        self.status = False
        self.running = False

    def write(self, data):
        """
        Schreibt Daten in den Buffer.
        
        :param data: Die zu schreibenden Daten.
        :type data: str
        """
        self.buffer.append(data)

    def readline(self):
        """
        Liest eine Zeile aus dem Buffer.
        
        :return: Die gelesene Zeile.
        :rtype: str
        """
        if self.buffer:
            return self.buffer.pop(0)
        return b""

    def start_generating_data(self):
        """
        Startet die kontinuierliche Generierung von Sinuswellen-Daten.
        """
        def generate_data():
            t = 0
            while self.running:
                t += 0.01
                value = np.sin(2 * np.pi * 1 * t)  # 1 Hz Sinuswelle
                self.buffer.append(f"{value}\n".encode('utf-8'))
                time.sleep(0.01)
        
        threading.Thread(target=generate_data, daemon=True).start()
        

    def __getattr__(self, name):
        """
        Ermöglicht MockSerial so zu tun, als hätte es jedes beliebige Attribut.
        
        :param name: Der Name des Attributs.
        :type name: str
        :return: Gibt immer None zurück.
        """
        return None

class SerielleKom:
    """
    Eine Klasse zur Verwaltung der seriellen Kommunikation.
    """
    def __init__(self, port='COM1', baudrate=9600, use_mock=False):
        """
        Initialisiert die serielle Verbindung.
        
        :param port: Der COM-Port.
        :type port: str
        :param baudrate: Die Baudrate.
        :type baudrate: int
        :param use_mock: Wenn True, wird MockSerial verwendet.
        :type use_mock: bool
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.use_mock = use_mock
    
    def verbinden(self):
        """
        Verbindet mit dem angegebenen seriellen Port oder mit dem MockSerial.
        
        :return: True, wenn die Verbindung erfolgreich war, sonst False.
        :rtype: bool
        """
        try:
            if self.use_mock:
                self.ser = MockSerial(self.port, self.baudrate)
                self.ser.open()  # Ensure the mock port is "opened"
                return True
            else:
                self.ser = serial.Serial(self.port, self.baudrate)
                
            if self.ser.is_open:
                return True
        except serial.SerialException as e:
            return False
        except AttributeError:
            # Handling for MockSerial which does not have is_open attribute initially
            self.ser.open()  # Ensure the mock port is "opened"
            return True

    def trennen(self):
        """
        Trennt die serielle Verbindung.
        
        :return: True, wenn die Verbindung erfolgreich getrennt wurde, sonst False.
        :rtype: bool
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            return True
        return False

    def lese_daten(self):
        """
        Liest Daten von MockSerial und dekodiert sie.
        
        :return: Die gelesenen Daten als Array.
        :rtype: np.ndarray
        """
        if self.ser and self.ser.is_open:
            try:
                zeile = self.ser.readline().decode('utf-8').strip()
                if zeile:
                    daten = np.array([float(zeile)])
                    return daten
            except Exception as e:
                return None
        return None

    def schreibe_daten(self, daten):
        """
        Schreibt Daten zum seriellen Port.
        
        :param daten: Die zu schreibenden Daten.
        :type daten: str
        """
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(daten.encode('utf-8'))
            except Exception as e:
                pass

if __name__ == "__main__":
    # Hauptprogramm zur Demonstration der seriellen Kommunikation
    kom = SerielleKom(port='COM3', baudrate=9600, use_mock=True)
    if kom.verbinden():
        for _ in range(10):  # Lese 10 Zeilen
            daten = kom.lese_daten()
            if daten is not None:
                print(f"Empfangene Daten: {daten}")
            time.sleep(1)
        kom.trennen()

    # Startet die GUI-Anwendung
    root = tk.Tk()
    app = SerielleApp(master=root)
    root.mainloop()
