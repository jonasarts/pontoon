from __future__ import absolute_import

import os

import pytest

from mock import patch

from pontoon.base.models import ProjectLocale
from pontoon.test.factories import (
    ChangedEntityLocaleFactory,
    EntityFactory,
    ProjectLocaleFactory,
    RepositoryFactory,
    ResourceFactory,
)


@pytest.mark.django_db
def test_project_commit_no_repos(project_a):
    """can_commit should be False if there are no repos."""

    assert project_a.repositories.count() == 0
    assert not project_a.can_commit


@pytest.mark.django_db
def test_project_commit_false(project_a, repo_file):
    """
    can_commit should be False if there are no repo xthat can be
    committed to.
    """
    assert project_a.repositories.first().type == "file"
    assert not project_a.can_commit


@pytest.mark.django_db
def test_project_commit_true(project_a, repo_git):
    """
    can_commit should be True if there is a repo that can be
    committed to.
    """
    assert project_a.repositories.first().type == "git"
    assert project_a.can_commit


@pytest.mark.django_db
def test_project_type_no_repos(project_a):
    """If a project has no repos, repository_type should be None."""
    assert project_a.repository_type is None


@pytest.mark.django_db
def test_project_type_multi_repos(project_a, repo_git, repo_hg):
    """
    If a project has repos, return the type of the repo created
    first.
    """
    assert project_a.repositories.first().type == "git"
    assert project_a.repository_type == "git"


@pytest.mark.django_db
def test_project_repo_path_none(project_a):
    """
    If the project has no matching repositories, raise a ValueError.
    """
    with pytest.raises(ValueError):
        project_a.repository_for_path("doesnt/exist")


@pytest.mark.django_db
def test_project_repo_for_path(project_a):
    """
    Return the first repo found with a checkout path that contains
    the given path.
    """
    repos = [
        RepositoryFactory.create(type="file", project=project_a, url="testrepo%s" % i,)
        for i in range(0, 3)
    ]
    path = os.path.join(repos[1].checkout_path, "foo", "bar")
    assert project_a.repository_for_path(path) == repos[1]


@pytest.mark.django_db
def test_project_needs_sync(project_a, project_b, locale_a):
    """
    Project.needs_sync should be True if ChangedEntityLocale objects
    exist for its entities or if Project has unsynced locales.
    """
    resource = ResourceFactory.create(project=project_a, path="resourceX.po")
    entity = EntityFactory.create(resource=resource, string="entityX")

    assert not project_a.needs_sync
    ChangedEntityLocaleFactory.create(entity=entity, locale=locale_a)
    assert project_a.needs_sync

    assert not project_b.needs_sync
    assert project_b.unsynced_locales == []
    del project_b.unsynced_locales
    ProjectLocaleFactory.create(
        project=project_b, locale=locale_a,
    )
    assert project_b.needs_sync == [locale_a]


@pytest.mark.django_db
def test_project_latest_activity_with_latest(project_a, translation_a):
    """
    If the project has a latest_translation and no locale is given,
    return it.
    """
    assert project_a.latest_translation == translation_a
    assert project_a.get_latest_activity() == translation_a.latest_activity


@pytest.mark.django_db
def test_project_latest_activity_without_latest(project_a):
    assert project_a.latest_translation is None
    assert project_a.get_latest_activity() is None


@pytest.mark.django_db
def test_project_latest_activity_with_locale(locale_a, project_a):
    with patch.object(ProjectLocale, "get_latest_activity") as m:
        m.return_value = "latest"
        assert project_a.get_latest_activity(locale=locale_a) == "latest"
        assert m.call_args[0] == (project_a, locale_a)
