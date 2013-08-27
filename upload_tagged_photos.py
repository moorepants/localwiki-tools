#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import getpass

import slumber
from gi.repository import GExiv2


class ImageUploader(object):

    _tmp_dir_name = '.localwiki'
    _file_extensions = ['.png', '.jpg', '.gif']

    def __init__(self, api_url, user_name=None, api_key=None):
        """Initializes the uploader.

        Parameters
        ==========
        api_url : string
            This should point to your API and have a trailing slash, e.g.
            'http://clevelandwiki.org/api/'.
        user_name : string, optional, default=None
            The user name for you API key. If you don't provide this here,
            then you will be prompted to enter it on initialization.
        api_key : string, optional, default=None
            The api_key for this user. If you don't provide this here, then
            you will be prompted to enter it on initialization.

        """

        if user_name is None:
            self.user_name = raw_input("What is your username?\n")
        else:
            self.user_name = user_name

        if api_key is None:
            self.api_key = getpass.getpass("What is your api_key?\n")
        else:
            self.api_key = api_key

        self.api = slumber.API(api_url, append_slash=False)

    def upload(self, main_keyword, *directories, **kwargs):
        """Uploads all the new files in the specified directories with the
        proper tags to localwiki and creates new pages if needed.

        Parameters
        ==========
        main_keyword : string
            The keyword embedd in Iptc.Application2.Keywords that identifies
            your image as one that belongs on your localwiki site, e.g.
            'cleveland wiki'.
        directories : str
            The directories to search for images.
        page_keyword_prefix : string, optional, default="page:"
            This is the prefix for the keyword embedded in your image which
            contains the page name where the image belongs, e.g. if you you
            image belongs on the front page then you keyword should look
            like "page:Front Page".

        """

        self.directories = list(directories)
        self.main_keyword = main_keyword
        if 'page_keyword_prefix' in kwargs.keys():
            self.page_keyword_prefix = kwargs['page_keyword_prefix']
        else:
            self.page_keyword_prefix = "page:"

        wiki_images = self.find_localwiki_images()

        for file_path, page_names in wiki_images.items():

            for page_name in page_names:

                page = self.create_page(page_name)
                image_name = os.path.split(file_path)[1]
                if not self.file_exists_on_server(image_name):
                    self.upload_image(page, file_path)
                    self.embed_image(page_name, image_name)
                else:
                    print("{} already exists on the localwiki.".format(file_path))

        print('Cleaning up image rotations.')
        self.remove_tmp_dirs(wiki_images.keys())
        print('Done.')

    def remove_tmp_dirs(self, file_paths):
        """Removes any of the temporary directories used to rotate images.

        Parameters
        ==========
        file_paths : list of strings
            The paths to the original files.

        """
        fondled_directories = set([os.path.split(path)[0] for path in
                                   file_paths])
        for directory in fondled_directories:
            tmp_dir = os.path.join(directory, self._tmp_dir_name)
            if os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir)

    def find_localwiki_images(self):
        """Returns a dictionary mapping local image paths to local wiki page
        names for all images in the provided directories that have the
        corret tags."""

        wiki_images = {}
        for directory in self.directories:
            wiki_images.update(self.find_localwiki_images_in_directory(directory))

        return wiki_images

    def find_localwiki_images_in_directory(self, directory):
        """Returns a dictionary mapping local image paths to local wiki page
        names.

        directory : string
            The path to the directory that should be scanned for localwiki
            images.

        """

        file_names = os.listdir(directory)

        wiki_images = {}

        for file_name in file_names:

            if True in [file_name.endswith(ext) for ext in
                        self._file_extensions]:
                metadata = GExiv2.Metadata(os.path.join(directory, file_name))
                keywords = \
                    metadata.get_tag_multiple('Iptc.Application2.Keywords')

                if self.main_keyword in keywords:

                    wiki_images[os.path.join(directory, file_name)] = \
                        [keyword.split(':')[1] for keyword in keywords if
                            keyword.startswith('page:')]

        return wiki_images

    def create_page(self, page_name):
        """Creates a new blank page on the server with the provided page
        name and returns the data recieved from the post, unless it already
        exists, in which case it returns the exsiting page.

        Parameters
        ==========
        page_name : string
            The name of the page to create.

        Returns
        =======
        page_dict : dictionary
            The response from the post.

        """

        page_dict = {
            "content": "<p>Please add some content to help describe this page.</p>",
            "name": page_name,
        }

        try:
            return self.api.page(page_name).get()
        except slumber.exceptions.HttpClientError:
            print("Creating the new page: {}".format(page_name))
            self.api.page.post(page_dict, username=self.user_name,
                               api_key=self.api_key)
            return self.api.page(page_name).get()

    def find_files_in_page(self, page_name):
        """Returns a list of dictionaries, one for each file, attached to a
        page and returns None if the page doesn't exist.

        Parameters
        ==========
        page_name : string
            The name of the page to create.

        Returns
        =======
        files : list of dictionaries or None
            The respons dictionaries, one for each file associated with the
            page. None if the page doesn't exist.

        """
        try:
            slug = self.api.page(page_name).get()['slug']
        except slumber.exceptions.HttpClientError:
            return None
        else:
            return self.api.file.get(slug=slug)['objects']

    def file_exists_on_server(self, file_name):
        """Returns true if the file already exists on the server.

        Parameters
        ==========
        file_name : string
            The name of the file, as stored in localwiki.


        """

        file_list = self.api.file.get()['objects']

        exists = False
        for file_dict in file_list:
            if file_dict['name'] == file_name:
                exists = True

        return exists

    def rotate_image(self, file_path):
        """Creates a temporary directory beside the file, copies the file
        into the directory, and rotates it based on the EXIF orientaiton
        data.

        Parameters
        ==========
        file_path : string
            The path to the image file.

        """
        directory, file_name = os.path.split(file_path)
        os.mkdir(os.path.join(directory, self._tmp_dir_name))
        tmp_file_path = os.path.join(directory, self._tmp_dir_name,
                                     file_name)
        shutil.copyfile(file_path, tmp_file_path)
        os.system("jhead -ft -autorot {}".format(tmp_file_path))

    def upload_image(self, page, file_path):
        """Uploads the image to the server.

        Parameters
        ==========
        page : dictionary
            The response dictionary for a page.
        file_path : string
            The path to the image file.

        """

        metadata = GExiv2.Metadata(file_path)

        directory, file_name = os.path.split(file_path)
        tmp_file_path = os.path.join(directory, 'tmp', file_name)

        try:
            with open(tmp_file_path):
                pass
        except IOError:
            rotated = False
        else:
            rotated = True

        if metadata['Exif.Image.Orientation'] != '1' and not rotated:
            self.rotate_image(file_path)
            image_path = tmp_file_path
        else:
            image_path = file_path

        with open(image_path, 'r') as image:
            print('Uploading {} to {}'.format(file_name, page['name']))
            self.api.file.post({'name': file_name, 'slug': page['slug']},
                               files={'file': image},
                               username=self.user_name,
                               api_key=self.api_key)
            print('Done.')

    def embed_image(self, page_name, image_name, caption='Caption me!'):
        """Appends HTML to the page that embeds the attached image.

        Parameters
        ==========
        page_name : string
            The name of the page to create.
        image_name : string
            The name of an image that is attached to the page.
        caption : string, optional, default='Caption me!'
            The caption that is displayed under the image.

        Returns
        =======
        page_response : dictionary
            The response from the patch.

        """
        files = self.find_files_in_page(page_name)
        page_info = self.api.page(page_name).get()

        current_content = page_info['content']
        html = \
"""
<p>
  <span class="image_frame image_frame_border">
    <img src="_files/{}" style="width: 300px; height: 225px;" />
    <span class="image_caption" style="width: 300px;">
      {}
    </span>
  </span>
</p>
""".format(image_name, caption)

        if (image_name in [f['name'] for f in files] and html not
                in current_content):
            self.api.page(page_name).patch({'content':
                current_content + html}, username=self.user_name,
                api_key=self.api_key)
            return self.api.page(page_name).get()
        else:
            print('Aborting image not embedding, do it manually.')
            return None

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description='Upload images to local wiki.')
    parser.add_argument('url', type=str,
        help="The API url with a trailing slash, e.g http://clevelandwiki.org/api/")
    parser.add_argument('keyword', type=str,
        help="The main keyword to look for, e.g. 'cleveland wiki'.")
    parser.add_argument('directories', type=str, narg='*',
        help="The directories to search.")
    parser.add_argument('--prefix', type=str,
        help="The keyword page name prefix, the default is 'page:'.")
    args = parser.parse_args()

    uploader = ImageUploader(args.url)

    if args.prefix:
        kwargs = {'page_keyword_prefix': args.prefix}
    else:
        kwargs = {}

    uploader.upload(args.keyword, *args.directories, **kwargs)
