#!/bin/bash
# drehteller.sh - Hilfsskript zum Verwalten des 360° Drehteller-Systems

case "$1" in
    start)
        sudo systemctl start drehteller360.service
        echo "360° Drehteller-System gestartet."
        ;;
    stop)
        sudo systemctl stop drehteller360.service
        echo "360° Drehteller-System gestoppt."
        ;;
    restart)
        sudo systemctl restart drehteller360.service
        echo "360° Drehteller-System neugestartet."
        ;;
    status)
        sudo systemctl status drehteller360.service
        ;;
    logs)
        sudo journalctl -u drehteller360.service -f
        ;;
    *)
        echo "Verwendung: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
exit 0
