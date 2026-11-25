import io
import json

from adres.cli import main


def test_single_address_json(capsys):
    assert main(["Caferağa Mah. Moda Cad. No:12 Kadıköy/İstanbul"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["district"] == "Kadıköy" and out["building_no"] == "12"


def test_line(capsys):
    main(["--line", "caferağa mh moda cd no 12 kadıköy istanbul"])
    assert capsys.readouterr().out.strip() == "Caferağa Mah. Moda Cad. No:12 Kadıköy/İstanbul"


def test_stdin_csv(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("Bornova İzmir\n\nÇankaya Ankara\n"))
    main(["--csv"])
    rows = capsys.readouterr().out.strip().splitlines()
    assert rows[0].startswith("input,province,district")
    assert rows[1].startswith("Bornova İzmir,İzmir,Bornova")
    assert len(rows) == 3


def test_stdin_jsonl(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("Bornova İzmir\nÇankaya Ankara\n"))
    main([])
    lines = [json.loads(x) for x in capsys.readouterr().out.splitlines()]
    assert [x["province"] for x in lines] == ["İzmir", "Ankara"]
