
import pytest

from zardoz import rolls


class TestSplitFilterTokens:

    @pytest.mark.parametrize('zop', rolls.OPS)
    def test_split_no_whitespace(self, zop):
        word = f'A{zop}B'
        tokens = rolls.split_tokens(word)

        assert len(tokens) == 3
        assert tokens[1] == zop

    @pytest.mark.parametrize('zop', rolls.OPS)
    def test_split_whitespace(self, zop):
        word = f'A {zop} B'
        tokens = rolls.split_tokens(word)

        assert len(tokens) == 7
        assert tokens[3] == zop
        assert tokens[0] == 'A'
        assert tokens[-1] == 'B'

    @pytest.mark.parametrize('zop', rolls.OPS)
    def test_split_filter_no_whitespace(self, zop):
        word = f'A{zop}B{zop}C'
        tokens = rolls.filter_tokens(rolls.split_tokens(word))

        assert len(tokens) == 5
