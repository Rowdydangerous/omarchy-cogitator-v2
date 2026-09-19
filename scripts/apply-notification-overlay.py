#!/usr/bin/env python3
"""Stamp the Cogitator herald layout onto an installed notifications clone.

Usage: apply-notification-overlay.py <Service.qml> <card-src>

Copies the vendored herald card over the clone's NotificationCard.qml and
re-anchors the popup column from top-right to top-center. Idempotent:
a marker comment records application; re-runs are no-ops. Fails loudly
if the stock anchor blocks are absent (upstream drift) so enable never
half-applies.
"""
import shutil
import sys
from pathlib import Path

MARKER = "// cogitator-v2-herald"

COLUMN_STOCK = """      ColumnLayout {
        id: popupColumn
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: popupWindow.popupPlacement.margins.top
        anchors.rightMargin: popupWindow.popupPlacement.margins.right
        spacing: Style.space(8)"""

COLUMN_HERALD = """      // cogitator-v2-herald: centered proclamations, non-modal mask.
      ColumnLayout {
        id: popupColumn
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: Math.round(parent.height * 0.22)
        width: Math.min(560, parent.width - 48)
        spacing: Style.space(8)"""

ALIGN_STOCK = """            Layout.preferredWidth: card.implicitWidth
            Layout.alignment: Qt.AlignRight"""
ALIGN_HERALD = """            Layout.preferredWidth: card.implicitWidth
            Layout.alignment: Qt.AlignHCenter"""

CARD_STOCK = """            NotificationCard {
              id: card
              anchors.right: parent.right"""
CARD_HERALD = """            NotificationCard {
              id: card
              anchors.horizontalCenter: parent.horizontalCenter"""


def main():
    service_path = Path(sys.argv[1])
    card_src = Path(sys.argv[2])
    text = service_path.read_text()
    lines = text.splitlines()
    if MARKER in (line.strip() for line in lines):
        print("herald overlay already applied")
        return 0
    herald_shaped = (
        "anchors.horizontalCenter: parent.horizontalCenter" in text
        and "Layout.alignment: Qt.AlignHCenter" in text
    )
    stock_shaped = (
        COLUMN_STOCK in text
        and ALIGN_STOCK in text
        and CARD_STOCK in text
    )
    if herald_shaped and not stock_shaped:
        # Styled by hand before management began: adopt by stamping the
        # receipt marker instead of failing.
        service_path.write_text(MARKER + "\n" + text)
        print("herald overlay adopted from existing styling")
        return 0
    for stock, herald, label in (
        (COLUMN_STOCK, COLUMN_HERALD, "popup column"),
        (ALIGN_STOCK, ALIGN_HERALD, "delegate alignment"),
        (CARD_STOCK, CARD_HERALD, "card anchors"),
    ):
        if stock not in text:
            print(f"DRIFT: stock {label} block not found in {service_path}", file=sys.stderr)
            return 1
        text = text.replace(stock, herald, 1)
    text = MARKER + "\n" + text
    card_dst = service_path.parent / "components" / "NotificationCard.qml"
    shutil.copyfile(card_src, card_dst)
    service_path.write_text(text)
    print("herald overlay applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
