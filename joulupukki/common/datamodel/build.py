import time
import json
import os

import pecan
import wsme
import wsme.types as wtypes

from joulupukki.common.database import mongo
from joulupukki.common.datamodel import types
#from joulupukki.common.datamodel.user import User
#from joulupukki.common.datamodel.project import Project
from joulupukki.common.datamodel.job import Job
from joulupukki.common.distros import supported_distros

source_types = wtypes.Enum(str, 'local', 'git')

class APIBuild(types.Base):
    source_url = wsme.wsattr(wtypes.text, mandatory=True)
    source_type = wsme.wsattr(source_types, mandatory=True, default="git")
    commit = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    branch = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    forced_distro = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    snapshot = wsme.wsattr(bool, mandatory=False, default=False)

class Build(APIBuild):
    id_ = wsme.wsattr(int, mandatory=False)
    created = wsme.wsattr(float, mandatory=False, default=None)
    finished = wsme.wsattr(float, mandatory=False, default=None)
    package_name = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    package_version = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    package_release = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    status = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    committer_name = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    committer_email = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    message = wsme.wsattr(wtypes.text, mandatory=False, default=None)
    # Link
    username = wsme.wsattr(wtypes.text, mandatory=False)
    project_name = wsme.wsattr(wtypes.text, mandatory=False)
    jobs = wsme.wsattr([Job], mandatory=False, default=None)
    job_count = wsme.wsattr(int, mandatory=False, default=0)




    def __init__(self, data=None, subojects=True):
        self.db_fields = ("job_count", "committer_email", "project_name", "package_name", "created",
                  "package_version", "status", "forced_distro", "package_release",
                  "username", "source_type", "finished", "snapshot", "branch", "commit",
                  "message", "source_url", "committer_name")
        if data is None:
            APIBuild.__init__(self)
        if isinstance(data, APIBuild):
            APIBuild.__init__(self, **data.as_dict())
        else:
            APIBuild.__init__(self, **data)
        self.user = None
        self.project = None
        if self.username and self.project_name:
            self.jobs = self.get_jobs()
        # fields on db

    @classmethod
    def sample(cls):
        return cls(
            source_url="https://github.com/kaji-project/shinken.git",
            source_type="git",
            branch="master",
        )



    def create(self):
        # Check required args
        required_args = ['source_url',
                         'source_type',
                        ]
        for arg in required_args:
            if not getattr(self, arg):
                # TODO handle error
                return False
        # Get last ids
        self.id_ = 1
        build_ids = [x["id_"] for x in mongo.builds.find({"username": self.username, "project_name": self.project_name}, ["id_"])]
        if build_ids is not None and build_ids != []:
            self.id_ = max(build_ids) + 1
        # Set attributes
        self.created = time.time()
        self.finished = None
        self.status = "created"

    def _save(self):
        """ Write project data on disk """
        # TODO delete me i'm useless
        return True






    def dumps(self):
        dump = self.as_dict()
        return dump



    def get_folder_path(self):
        """ Return build folder path"""
        return os.path.join(pecan.conf.workspace_path,
                            self.username,
                            self.project_name,
                            "builds",
                            str(self.id_))


    def get_output_folder_path(self, distro=None):
        """ Return build folder path"""
        if distro is None:
            path = os.path.join(pecan.conf.workspace_path,
                                self.username,
                                self.project_name,
                                "builds",
                                str(self.id_),
                                "output")
        else:
            path = os.path.join(pecan.conf.workspace_path,
                                self.username,
                                self.project_name,
                                "builds",
                                str(self.id_),
                                "output",
                                distro)
        return path




    def get_source_folder_path(self):
        """ Return project folder path"""
        return os.path.join(self.get_folder_path(),
                            "sources")



    def __setattr__(self, name, value):
        super(Build, self).__setattr__(name, value)
        if self.username and self.project_name and self.id_ and hasattr(self, 'db_fields'):
            if name in self.db_fields:
                mongo.builds.update({
                    "id_": self.id_,
                    "username": self.username,
                    "project_name": self.project_name},
                    {"$set": {name: value}},
                    upsert=True
                )


    def set_status(self, status):
        self.status = status



    def inc_job_count(self):
        self.job_count += 1


    def get_jobs(self):
        """ return all build ids """
        jobs_ids = [Job(x) for x in mongo.jobs.find({"username": self.username, "project_name": self.project_name, "build_id": int(self.id_)})]

        if jobs_ids:
            return sorted(jobs_ids, key=lambda x: x.id_)
        return []




    @classmethod
    def fetch(cls, project, id_, sub_objects=True):
        build_data = mongo.builds.find_one({"username": project.username,
                                            "project_name": project.name,
                                            "id_": int(id_)})
        build = cls(build_data, sub_objects)
        if sub_objects is False:
            delattr(build, 'jobs')
        return build

    def finishing(self):
        self.finished = time.time()
