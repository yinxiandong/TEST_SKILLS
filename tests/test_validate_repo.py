"""Exercise repository validation against isolated packages."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/validate-repo.py'


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def skill(self, directory, name=None, description='Review test cases.'):
        folder = self.root / directory
        folder.mkdir()
        (folder / 'SKILL.md').write_text(
            f'---\nname: {name or directory}\ndescription: {description}\n---\n\nReview the supplied cases.\n',
            encoding='utf-8')
        return folder

    def run_validator(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), *args],
                              capture_output=True, text=True, encoding='utf-8')

    def test_two_independent_skills_and_single_selection(self):
        self.skill('first-skill')
        second = self.skill('second-skill', description='|\n  Review cases.\n  Report missing coverage.')
        (self.root / 'docs').mkdir()
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Checked 2 skill(s)', result.stdout)
        (second / 'SKILL.md').write_text('broken', encoding='utf-8')
        self.assertEqual(self.run_validator('--skill', 'first-skill').returncode, 0)
        self.assertNotEqual(self.run_validator().returncode, 0)

    def test_missing_entrypoint(self):
        (self.root / 'missing-skill').mkdir()
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn('cannot read SKILL.md', result.stderr)

    def test_duplicate_names_and_directory_mismatch(self):
        self.skill('first-skill')
        self.skill('second-skill', name='first-skill')
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn('must match directory', result.stderr)
        self.assertIn('duplicate skill name', result.stderr)

    def test_invalid_metadata(self):
        for frontmatter in ('name: bad_name\ndescription: text',
                            'name: valid-skill\ndescription: ""',
                            'name: [unterminated',
                            'name: valid-skill\nname: valid-skill\ndescription: text',
                            '- a\n- list'):
            with self.subTest(frontmatter=frontmatter):
                folder = self.root / 'valid-skill'
                folder.mkdir(exist_ok=True)
                (folder / 'SKILL.md').write_text(f'---\n{frontmatter}\n---\nInstructions\n', encoding='utf-8')
                self.assertEqual(self.run_validator().returncode, 1)

    def test_empty_repository_and_missing_selection_fail(self):
        self.assertEqual(self.run_validator().returncode, 1)
        self.assertEqual(self.run_validator('--skill', 'missing-skill').returncode, 1)

    def test_selection_cannot_escape_root(self):
        self.assertEqual(self.run_validator('--skill', '../outside').returncode, 2)


if __name__ == '__main__':
    unittest.main()
