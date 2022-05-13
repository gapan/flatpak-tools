PREFIX ?= /usr/local
DESTDIR ?= /
PACKAGE_LOCALE_DIR ?= /usr/share/locale

.PHONY: all
all: mo desktop

.PHONY: mo
mo:
	for i in `ls po/*.po`; do \
		msgfmt $$i -o `echo $$i | sed "s/\.po//"`.mo; \
	done

.PHONY: desktop
desktop:
	intltool-merge po/ -d -u \
		flatpakref-installer.desktop.in flatpakref-installer.desktop

.PHONY: updatepo
updatepo:
	for i in `ls po/*.po`; do \
		msgmerge -UNs $$i po/flatpakref-installer.pot; \
	done
	rm -f po/*~

.PHONY: pot
pot:
	xgettext --from-code=utf-8 \
		-L Glade \
		-o po/flatpakref-installer.pot \
		src/flatpakref-installer.ui
	xgettext --from-code=utf-8 \
		-j \
		-L Python \
		-o po/flatpakref-installer.pot \
		src/flatpakref-installer.py
	intltool-extract --type="gettext/ini" \
		flatpakref-installer.desktop.in
	xgettext --from-code=utf-8 -j -L C -kN_ \
		-o po/flatpakref-installer.pot flatpakref-installer.desktop.in.h
	rm -f flatpakref-installer.desktop.in.h

.PHONY: clean
clean:
	rm -f po/*.mo
	rm -f po/*.po~
	rm -f flatpakref-installer.desktop

.PHONY: install
install: install-mime install-mo
	install -d -m 755 $(DESTDIR)/usr/bin
	install -d -m 755 $(DESTDIR)/usr/share/flatpak-tools
	install -d -m 755 $(DESTDIR)/usr/share/applications
	install -m 755 src/flatpakref-installer.py $(DESTDIR)/usr/bin/flatpakref-installer
	install -m 644 src/flatpakref-installer.ui $(DESTDIR)/usr/share/flatpak-tools/
	install -m 644 flatpakref-installer.desktop $(DESTDIR)/usr/share/applications/

.PHONY: install-mime
install-mime:
	install -d -m 755 $(DESTDIR)/usr/share/mime/packages
	install -d -m 755 $(DESTDIR)/usr/share/mimelnk/applications
	install -m 644 mime/flatpak.xml $(DESTDIR)/usr/share/mime/packages/
	install -m 644 mime/*.desktop $(DESTDIR)/usr/share/mimelnk/applications/

.PHONY: install-mo
install-mo:
	for i in `ls po/*.po|sed "s/po\/\(.*\)\.po/\1/"`; do \
		install -d -m 755 $(DESTDIR)/usr/share/locale/$$i/LC_MESSAGES; \
		install -m 644 po/$$i.mo $(DESTDIR)/usr/share/locale/$$i/LC_MESSAGES/flatpakref-installer.mo; \
	done

.PHONY: tx-pull
tx-pull:
	tx pull -a
	@for i in `ls po/*.po`; do \
		msgfmt --statistics $$i 2>&1 | grep "^0 translated" > /dev/null \
			&& rm $$i || true; \
	done
	@rm -f messages.mo

.PHONY: tx-pull-f
tx-pull-f:
	tx pull -a -f
	@for i in `ls po/*.po`; do \
		msgfmt --statistics $$i 2>&1 | grep "^0 translated" > /dev/null \
			&& rm $$i || true; \
	done
	@rm -f messages.mo

.PHONY: stat
stat:
	@for i in `ls po/*.po`; do \
		echo "Statistics for $$i:"; \
		msgfmt --statistics $$i 2>&1; \
		echo; \
	done
	@rm -f messages.mo

