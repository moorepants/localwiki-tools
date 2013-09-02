#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library
import os
import shutil
import getpass

# external libraries
import slumber
from gi.repository import GExiv2
from PIL import Image


class ImageUploader(object):

    _tmp_dir_name = '.localwiki'
    # The code may only work with jpegs do to reliance on Exif metadata.
    _file_extensions = ['.png', '.jpg', '.gif', '.jpeg']
    _stub_page_content = "<p>This page is a stub, please add some content to help describe this page.</p>"

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
            The keyword embed in Iptc.Application2.Keywords that identifies
            your image as one that belongs on your localwiki site, e.g.
            'cleveland wiki'.
        directories : string
            The paths to directories to search for images.
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

            metadata = GExiv2.Metadata(file_path)

            tmp_file_path = self.create_tmp_image(file_path)

            self.resize_image_to_1024(file_path, tmp_file_path)

            if metadata['Exif.Image.Orientation'] != '1':
                self.rotate_image(tmp_file_path)

            aspect_ratio = float(metadata.get_pixel_width()) / \
                float(metadata.get_pixel_height())

            # Each file could have multple destination pages.
            for page_name in page_names:

                page = self.create_page(page_name)
                image_name = os.path.split(file_path)[1]

                # TODO : This check should be "if file exists on a page",
                # as it stands this probably wouldn't allow uploads to
                # multiple pages.
                if not self.file_exists_on_server(image_name):

                    self.upload_image(page, tmp_file_path)

                    if 'Iptc.Application2.Caption' in metadata.get_iptc_tags():
                        self.embed_image(page_name, image_name, aspect_ratio,
                            caption=metadata['Iptc.Application2.Caption'])
                    else:
                        self.embed_image(page_name, image_name, aspect_ratio)
                else:
                    print("Skipping {}, it already exists on the localwiki.".format(file_path))

        print('Cleaning up temporary images.')
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
        correct tags."""

        wiki_images = {}
        for directory in self.directories:
            wiki_images.update(self.find_localwiki_images_in_directory(directory))

        return wiki_images

    def find_localwiki_images_in_directory(self, directory):
        """Returns a dictionary mapping local image paths of files in the
        given directory to local wiki page names.

        Parameters
        ==========
        directory : string
            The path to the directory that should be scanned for localwiki
            images.

        Returns
        =======
        wiki_images : dictionary
            The key is the path to the images which have the main keyword
            and the associated value is a list of localwiki page names this
            image should be associated with.

        """

        file_names = os.listdir(directory)

        wiki_images = {}

        for file_name in file_names:

            if True in [file_name.endswith(ext) for ext in
                        self._file_extensions]:
                metadata = GExiv2.Metadata(os.path.join(directory, file_name))
                keywords = \
                    metadata.get_tag_multiple('Iptc.Application2.Keywords')

                # TODO : What happens if the image only has the
                # main_keyword and the page list is empty?

                if self.main_keyword in keywords:

                    wiki_images[os.path.join(directory, file_name)] = \
                        [keyword.split(':')[1] for keyword in keywords if
                            keyword.startswith('page:')]

        return wiki_images

    def create_page(self, page_name):
        """Creates a new blank page on the server with the provided page
        name and returns the data received from the post, unless it already
        exists, in which case it returns the existing page.

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
            "content": self._stub_page_content,
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
            The response dictionaries, one for each file associated with the
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

    def create_tmp_image(self, file_path):
        """Makes a copy of the file in a tmp directory beside the file.

        Parameters
        ==========
        file_path : string
            The path to the image file.

        Returns
        =======
        tmp_file_path : string
            The path to the temporary image copy.

        """

        directory, file_name = os.path.split(file_path)
        tmp_directory = os.path.join(directory, self._tmp_dir_name)
        tmp_file_path = os.path.join(tmp_directory, file_name)

        if not os.path.isdir(tmp_directory):
            os.mkdir(tmp_directory)

        shutil.copyfile(file_path, tmp_file_path)

        return tmp_file_path

    @staticmethod
    def rotate_image(file_path):
        """Rotate and image to the correct orienation based on the EXIF
        orientation data.

        Parameters
        ==========
        file_path : string
            The path to the image file.

        """
        # -ft : sets the filesystem timestamp to the Exif timestamp
        # -autorot : rotates the image so it is upright and then sets the
        # orientation tag to 1
        os.system("jhead -ft -autorot {}".format(file_path))

        # TODO : Change this to a PIL call?:
        # http://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image

    @staticmethod
    def resize_image_to_1024(parent_file_path, file_path):
        """Resizes the image to 1024 if it is larger in width.

        Parameters
        ==========
        parent_file_path : string
            The path to the original image file with all the metadata.
        file_path : string
            The path to the temporary image file that should be resized.

        Notes
        =====
        Do this before rotating the image because it is only based on width.

        """
        img = Image.open(file_path)
        width, height = img.size
        aspect_ratio = float(width) / float(height)
        max_width = 1024
        if width > max_width:

            reduced_size = max_width, int(max_width / aspect_ratio)
            img.thumbnail(reduced_size, Image.ANTIALIAS)
            img.save(file_path, img.format)

            # Copy all metadata from parent file to the resized file
            os.system('jhead -te {} {}'.format(parent_file_path, file_path))

            metadata = GExiv2.Metadata(file_path)
            if (metadata.get_pixel_width() != reduced_size[0] or
                metadata.get_pixel_height() != reduced_size[1]):

                metadata.set_pixel_width(reduced_size[0])
                metadata.set_pixel_height(reduced_size[1])
                metadata.save_file()

    def upload_image(self, page, file_path):
        """Uploads the image to the server and associates it with the given
        page.

        Parameters
        ==========
        page : dictionary
            The response dictionary for a page.
        file_path : string
            The path to the image file.

        """

        with open(file_path, 'r') as image:

            print('Uploading {} to the {} page'.format(file_path,
                                                       page['name']))

            self.api.file.post({'name': os.path.split(file_path)[1],
                                'slug': page['slug']},
                               files={'file': image},
                               username=self.user_name,
                               api_key=self.api_key)
            print('Done.')

    def embed_image(self, page_name, image_name, image_aspect_ratio,
                    caption='Caption me!'):
        """Appends HTML to the page that embeds the attached image.

        Parameters
        ==========
        page_name : string
            The name of the page to embed the image too.
        image_name : string
            The name of an image that is already attached to the page.
        image_aspect_ratio : float
            The ratio of width to height of the rotated image.
        caption : string, optional, default='Caption me!'
            The caption that is displayed under the image.

        Returns
        =======
        page_response : dictionary
            The response from the patch.

        """
        files = self.find_files_in_page(page_name)
        page_info = self.api.page(page_name).get()

        thumbnail_width = 300  # pixels
        thumbnail_height = int(thumbnail_width / image_aspect_ratio)

        current_content = page_info['content']
        # TODO: Rotated images seem to have confused exifs on the web site.
        html = \
"""
<p>
  <span class="image_frame image_frame_border">
    <img src="_files/{}" style="width: 300px; height: {}px;" />
    <span class="image_caption" style="width: 300px;">
      {}
    </span>
  </span>
</p>
""".format(image_name, thumbnail_height, caption)

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
    import ConfigParser

    parser = argparse.ArgumentParser(
        description='Upload images to local wiki.')

    parser.add_argument('--url', type=str, default=None,
        help="The API url with a trailing slash, e.g http://clevelandwiki.org/api/")

    parser.add_argument('--keyword', type=str, default=None,
        help="The main keyword to look for, e.g. 'cleveland wiki'.")

    parser.add_argument('--prefix', type=str, default=None,
        help="The keyword page name prefix, the default is 'page:'.")

    parser.add_argument('--username', type=str, default=None,
        help="The user name for API access.")

    parser.add_argument('--apikey', type=str, default=None,
        help="The api key for API access.")

    parser.add_argument('directories', type=str, nargs='*',
        help="The directories to search.")

    args = parser.parse_args()

    if not args.keyword:
        config = ConfigParser.ConfigParser()
        config.read('test.cfg')
        api_url = config.get('localwiki', 'api_url')
        init_kwargs = {'user_name': config.get('localwiki', 'user_name'),
                       'api_key': config.get('localwiki', 'api_key')}
        main_keyword = config.get('localwiki', 'main_keyword')
        upload_kwargs = {'page_keyword_prefix':
                         config.get('localwiki', 'page_keyword_prefix')}
    else:
        api_url = args.url
        main_keyword = args.keyword

        init_kwargs = {}

        if args.username:
            init_kwargs.update({'user_name': args.username})

        if args.apikey:
            init_kwargs.update({'api_key': args.apikey})

        upload_kwargs = {}

        if args.prefix:
            upload_kwargs.update({'page_keyword_prefix': args.prefix})

    uploader = ImageUploader(api_url, **init_kwargs)
    uploader.upload(main_keyword, *args.directories, **upload_kwargs)
