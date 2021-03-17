from chitty.cli import run


def test_default_runs_without_instrument(mocker):
    fake_run = mocker.Mock()
    mocker.patch('chitty.cli.trio.run', fake_run)
    mocker.patch(
        'chitty.cli.parse_args', mocker.Mock(return_value=mocker.Mock(instrument=False))
    )
    run()
    fake_run.assert_called_once()
    assert 'instruments' not in fake_run.call_args.kwargs
